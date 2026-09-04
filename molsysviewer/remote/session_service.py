"""Authenticated single-user session surface for explicit rendering placement."""

from __future__ import annotations

import asyncio
import hmac
import json
import secrets
import tempfile
from collections import OrderedDict, deque
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web

from .internal_worker_host import InternalRenderWorkerHost
from .protocol import validate_signaling_packet
from .render_worker import RenderWorkerConfig, RenderWorkerDiagnostics
from .view_channel import RemoteViewChannel

_SESSION_SUBPROTOCOL = "molsysviewer-session-v1"
_SERVER_CLIENT_CAPABILITIES = frozenset(
    {"command-origin", "input-send", "video-receive", "workbench"}
)
_LOCAL_CLIENT_CAPABILITIES = frozenset(
    {"command-origin", "input-send", "render", "structure-receive", "workbench"}
)
_VIEWER_JS = Path(__file__).resolve().parents[1] / "viewer.js"
_MAX_UPLOAD_BYTES = 64 * 1024 * 1024
_MAX_AUTH_BODY_BYTES = 4 * 1024
_MAX_CLIENT_MESSAGE_BYTES = 1024 * 1024
_MAX_AUTH_FAILURES = 8
_AUTH_FAILURE_WINDOW_SECONDS = 60.0
_UPLOAD_SUFFIXES = frozenset({".pdb", ".ent", ".cif", ".mmcif", ".gro", ".mol2", ".sdf", ".h5msm"})

_CLIENT_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MolSysViewer remote session</title>
  <style>
    html, body, #molsysviewer-client { width: 100%; height: 100%; margin: 0; overflow: hidden; }
    body { background: #080b10; }
  </style>
</head>
<body>
  <div id="molsysviewer-client"></div>
  <script type="module" src="/session/client-bootstrap.js"></script>
</body>
</html>
"""

_CLIENT_BOOTSTRAP = """const fragment = new URLSearchParams(location.hash.slice(1));
const token = fragment.get('token');
if (token) {
    const auth = await fetch('./auth', {
        method: 'POST', credentials: 'same-origin', cache: 'no-store',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }),
    });
    if (!auth.ok) throw new Error(`remote-session authentication failed: ${auth.status}`);
    history.replaceState(null, '', location.pathname);
}
const configResponse = await fetch('./config', { credentials: 'same-origin', cache: 'no-store' });
if (!configResponse.ok) throw new Error(`remote-session config failed: ${configResponse.status}`);
const config = await configResponse.json();
const module = await import('./viewer.js');
const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
const boot = config.renderOn === 'client'
    ? module.bootRemoteRenderedClient
    : module.bootRemoteBrowserClient;
globalThis.__molsysviewerRemoteClient = await boot({
    el: document.querySelector('#molsysviewer-client'),
    websocketUrl: `${scheme}//${location.host}/session/ws`,
    ...config,
});
"""


class RemoteSessionService:
    """Compose one Python authority and one browser/Qt web attachment."""

    def __init__(
        self,
        worker_config: RenderWorkerConfig | None = None,
        *,
        render_on: str = "server",
        listen_host: str = "127.0.0.1",
        listen_port: int = 0,
        ice_servers: Sequence[Mapping[str, Any]] = (),
    ) -> None:
        if listen_host not in {"127.0.0.1", "localhost"}:
            raise ValueError(
                "RRS2 loopback service requires listen_host='127.0.0.1'; "
                "external binding needs the later TLS/reverse-proxy configuration"
            )
        if isinstance(ice_servers, (str, bytes)):
            raise TypeError("ice_servers must be a sequence of mappings")
        if render_on not in {"client", "server"}:
            raise ValueError("render_on must be 'client' or 'server'")
        if (
            not isinstance(listen_port, int)
            or isinstance(listen_port, bool)
            or not 0 <= listen_port <= 65535
        ):
            raise ValueError("listen_port must be an integer between 0 and 65535")
        self.render_on = render_on
        self._ice_servers = tuple(dict(item) for item in ice_servers)
        self._client_render_queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue(256)
        self._host = (
            InternalRenderWorkerHost(worker_config) if render_on == "server" else None
        )
        self.channel = (
            self._host.channel
            if self._host is not None
            else RemoteViewChannel(
                self._enqueue_client_render_control,
                render_on="client",
                send_data=self._enqueue_client_render_data,
            )
        )
        self.channel.download_publisher = self._publish_download
        self._listen_host = listen_host
        self._listen_port = listen_port
        self._port: int | None = None
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._token = secrets.token_urlsafe(32)
        self._cookie_name = f"molsysviewer_session_{secrets.token_hex(8)}"
        self._auth_failures: deque[float] = deque(maxlen=_MAX_AUTH_FAILURES)
        self._client_socket: web.WebSocketResponse | None = None
        self._client_registered = False
        self._closed = False
        self.failure: str | None = None
        self.last_client_error: str | None = None
        self.client_registered = asyncio.Event()
        self.client_registration_count = 0
        self.video_connected = asyncio.Event()
        self.input_channel_open = asyncio.Event()
        self.worker_input_received = asyncio.Event()
        self.client_render_ready = asyncio.Event()
        self.client_structure_complete = asyncio.Event()
        if self._host is not None:
            self._host.worker_signal_sink = self._forward_worker_signal
            self._host.worker_peer_state_sink = self._handle_worker_peer_state
            self._host.client_control_sink = self._forward_client_control
        self._client_control_queue: asyncio.Queue[
            tuple[dict[str, Any], asyncio.Future[None]]
        ] = asyncio.Queue(256)
        self._pending_client_control: set[asyncio.Future[None]] = set()
        self._client_control_pump: asyncio.Task[None] | None = None
        self._worker_monitor_task: asyncio.Task[None] | None = None
        self._worker_recovery_lock = asyncio.Lock()
        self.worker_recovery_count = 0
        self.worker_recovery_state = "idle"
        self._downloads: OrderedDict[str, tuple[str, str, bytes]] = OrderedDict()

    @property
    def worker_host(self) -> InternalRenderWorkerHost:
        if self._host is None:
            raise RuntimeError("client rendering has no render worker")
        return self._host

    @property
    def client_endpoint_id(self) -> str:
        return f"browser-client:{self.channel.router.session_id}"

    @property
    def client_actor_id(self) -> str:
        return f"human:{self.channel.router.session_id}"

    @property
    def origin(self) -> str:
        if self._port is None:
            raise RuntimeError("remote session service has not started")
        return f"http://{self._listen_host}:{self._port}"

    @property
    def client_url(self) -> str:
        return f"{self.origin}/session/client#token={self._token}"

    async def start(self) -> str:
        if self._closed:
            raise RuntimeError("remote session service is closed")
        if self._runner is not None:
            return self.client_url
        _ = self.channel.router
        if self._host is not None:
            await self._host.start()
        app = web.Application(client_max_size=_MAX_UPLOAD_BYTES + 1024 * 1024)
        app.add_routes(
            [
                web.get("/session/client", self._serve_client),
                web.get("/session/client-bootstrap.js", self._serve_bootstrap),
                web.post("/session/auth", self._authenticate),
                web.get("/session/config", self._serve_config),
                web.get("/session/viewer.js", self._serve_viewer),
                web.get("/session/download/{artifact_id}", self._serve_download),
                web.post("/session/upload", self._receive_upload),
                web.get("/session/ws", self._accept_client),
            ]
        )
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, self._listen_host, self._listen_port)
        try:
            await site.start()
            sockets = getattr(site._server, "sockets", None)  # noqa: SLF001
            if not sockets:
                raise RuntimeError("remote session service did not bind a socket")
            self._port = int(sockets[0].getsockname()[1])
        except BaseException:
            await runner.cleanup()
            if self._host is not None:
                await self._host.close()
            raise
        self._runner = runner
        self._site = site
        return self.client_url

    async def launch_worker(self) -> RenderWorkerDiagnostics:
        if self._host is None:
            raise RuntimeError("render_on='client' does not launch a render worker")
        if self._runner is None:
            await self.start()
        diagnostics = await self._host.launch_worker()
        if self._worker_monitor_task is None:
            self._worker_monitor_task = asyncio.create_task(
                self._monitor_worker(), name="molsysviewer-render-worker-monitor"
            )
        return diagnostics

    async def _send_session_state(self, state: str, detail: str | None = None) -> None:
        socket = self._client_socket
        if socket is None or socket.closed or not self._client_registered:
            return
        payload: dict[str, Any] = {"kind": "session-state", "state": state}
        if detail:
            payload["detail"] = detail
        await socket.send_json(payload)

    async def _recover_worker(self, reason: str) -> None:
        host = self.worker_host
        async with self._worker_recovery_lock:
            if self._closed:
                return
            self.worker_recovery_state = "recovering"
            self.video_connected.clear()
            self.input_channel_open.clear()
            await self._send_session_state("recovering", reason)
            try:
                await host.restart_worker()
                if self._client_registered:
                    host.send_worker_wire(
                        {
                            "kind": "peer-start",
                            "clientEndpointId": self.client_endpoint_id,
                            "actorId": self.client_actor_id,
                            "iceServers": list(self._ice_servers),
                        }
                    )
            except Exception as error:
                self.worker_recovery_state = "failed"
                self.failure = f"render-worker recovery failed: {error}"
                await self._send_session_state("failed", self.failure)
                raise
            self.worker_recovery_count += 1
            self.worker_recovery_state = "recovered"
            await self._send_session_state("recovered")

    async def _monitor_worker(self) -> None:
        host = self.worker_host
        try:
            while not self._closed:
                await asyncio.sleep(0.5)
                state = await host.worker.refresh_state()
                process_failed = state == "failed"
                transport_failed = state == "ready" and not host.worker_connected.is_set()
                if not process_failed and not transport_failed:
                    continue
                reason = host.worker.failure or host.failure or (
                    "render-worker transport disconnected"
                )
                try:
                    await self._recover_worker(reason)
                except Exception:
                    return
        except asyncio.CancelledError:
            raise

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._worker_monitor_task is not None:
            self._worker_monitor_task.cancel()
            await asyncio.gather(self._worker_monitor_task, return_exceptions=True)
            self._worker_monitor_task = None
        socket = self._client_socket
        if socket is not None and not socket.closed:
            try:
                await socket.send_json({"kind": "session-closing"})
            except ConnectionResetError:
                pass
            await socket.close(code=1001, message=b"session closed")
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._site = None
            self._port = None
        if self._host is not None:
            self._host.worker_signal_sink = None
            self._host.worker_peer_state_sink = None
            self._host.client_control_sink = None
        if self._client_control_pump is not None:
            self._client_control_pump.cancel()
            await asyncio.gather(self._client_control_pump, return_exceptions=True)
            self._client_control_pump = None
        for completion in tuple(self._pending_client_control):
            completion.cancel()
        self._pending_client_control.clear()
        self._downloads.clear()
        self.channel.download_publisher = None
        if self._host is not None:
            await self._host.close()
        else:
            self.channel.close()

    def _authorized(self, request: web.Request) -> bool:
        supplied = request.cookies.get(self._cookie_name, "")
        return bool(supplied) and hmac.compare_digest(supplied, self._token)

    def _auth_rate_limited(self) -> bool:
        now = asyncio.get_running_loop().time()
        while (
            self._auth_failures
            and now - self._auth_failures[0] >= _AUTH_FAILURE_WINDOW_SECONDS
        ):
            self._auth_failures.popleft()
        return len(self._auth_failures) >= _MAX_AUTH_FAILURES

    def _record_auth_failure(self) -> None:
        self._auth_failures.append(asyncio.get_running_loop().time())

    async def _serve_client(self, request: web.Request) -> web.Response:
        response = web.Response(text=_CLIENT_HTML, content_type="text/html")
        response.headers.update(self._security_headers())
        return response

    async def _serve_bootstrap(self, request: web.Request) -> web.Response:
        response = web.Response(text=_CLIENT_BOOTSTRAP, content_type="text/javascript")
        response.headers.update(self._security_headers())
        return response

    async def _authenticate(self, request: web.Request) -> web.Response:
        if request.headers.get("Origin") != self.origin:
            raise web.HTTPForbidden()
        try:
            if (
                request.content_length is not None
                and request.content_length > _MAX_AUTH_BODY_BYTES
            ):
                raise web.HTTPRequestEntityTooLarge(
                    max_size=_MAX_AUTH_BODY_BYTES,
                    actual_size=request.content_length,
                )
            try:
                body = await request.content.readexactly(_MAX_AUTH_BODY_BYTES + 1)
            except asyncio.IncompleteReadError as incomplete:
                body = incomplete.partial
            else:
                raise web.HTTPRequestEntityTooLarge(
                    max_size=_MAX_AUTH_BODY_BYTES,
                    actual_size=len(body),
                )
            value = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            if self._auth_rate_limited():
                raise web.HTTPTooManyRequests(headers={"Retry-After": "60"}) from error
            self._record_auth_failure()
            raise web.HTTPBadRequest() from error
        supplied = value.get("token", "") if isinstance(value, Mapping) else ""
        authenticated = isinstance(supplied, str) and hmac.compare_digest(
            supplied, self._token
        )
        if not authenticated:
            if self._auth_rate_limited():
                raise web.HTTPTooManyRequests(headers={"Retry-After": "60"})
            self._record_auth_failure()
            raise web.HTTPForbidden()
        self._auth_failures.clear()
        response = web.json_response({"authenticated": True})
        response.set_cookie(
            self._cookie_name,
            self._token,
            httponly=True,
            samesite="Strict",
            path="/session",
        )
        response.headers.update(self._security_headers())
        return response

    async def _serve_config(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPForbidden()
        response = web.json_response(
            {
                "viewerId": self.channel.router.viewer_id,
                "sessionId": self.channel.router.session_id,
                "endpointId": self.client_endpoint_id,
                "actorId": self.client_actor_id,
                "renderOn": self.render_on,
                "workerEndpointId": self._host.endpoint_id if self._host else None,
                "iceServers": list(self._ice_servers),
            }
        )
        response.headers.update(self._security_headers())
        return response

    async def _serve_viewer(self, request: web.Request) -> web.StreamResponse:
        if not self._authorized(request):
            raise web.HTTPForbidden()
        response = web.FileResponse(_VIEWER_JS)
        response.content_type = "text/javascript"
        response.headers.update(self._security_headers())
        return response

    def _publish_download(self, filename: str, media_type: str, data: bytes) -> str:
        if not isinstance(data, bytes) or not data:
            raise ValueError("download artifact must contain bytes")
        if len(data) > 24 * 1024 * 1024:
            raise ValueError("download artifact exceeds the 24 MiB session limit")
        artifact_id = secrets.token_urlsafe(24)
        basename = Path(filename).name
        safe_filename = "".join(
            character
            if character.isascii() and (character.isalnum() or character in {".", "_", "-"})
            else "_"
            for character in basename
        ) or "molsysviewer-download"
        self._downloads[artifact_id] = (safe_filename, str(media_type), data)
        while len(self._downloads) > 4:
            self._downloads.popitem(last=False)
        return f"/session/download/{artifact_id}"

    async def _serve_download(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPForbidden()
        artifact = self._downloads.get(request.match_info["artifact_id"])
        if artifact is None:
            raise web.HTTPNotFound()
        filename, media_type, data = artifact
        response = web.Response(body=data, content_type=media_type)
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers.update(self._security_headers())
        return response

    async def _receive_upload(self, request: web.Request) -> web.Response:
        if not self._authorized(request) or request.headers.get("Origin") != self.origin:
            raise web.HTTPForbidden()
        if not request.content_type.startswith("multipart/"):
            raise web.HTTPUnsupportedMediaType()

        reader = await request.multipart()
        field = await reader.next()
        if field is None or field.name != "file" or not field.filename:
            raise web.HTTPBadRequest(text="upload requires one file field")
        original_filename = Path(field.filename).name
        suffix = Path(original_filename).suffix.lower()
        if suffix not in _UPLOAD_SUFFIXES:
            raise web.HTTPUnsupportedMediaType(
                text=f"unsupported molecular file suffix: {suffix or '<none>'}"
            )

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=suffix, prefix="molsysviewer-upload-", delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                size = 0
                while chunk := await field.read_chunk(size=256 * 1024):
                    size += len(chunk)
                    if size > _MAX_UPLOAD_BYTES:
                        raise web.HTTPRequestEntityTooLarge(
                            max_size=_MAX_UPLOAD_BYTES, actual_size=size
                        )
                    temporary.write(chunk)
            if size == 0:
                raise web.HTTPBadRequest(text="uploaded molecular file is empty")
            if await reader.next() is not None:
                raise web.HTTPBadRequest(text="upload accepts exactly one file")
            try:
                result = dict(
                    self.channel.consume_upload(str(temporary_path), original_filename)
                )
            except Exception as error:
                response = web.json_response(
                    {"uploaded": False, "message": str(error)}, status=422
                )
            else:
                response = web.json_response({"uploaded": True, **result})
            response.headers.update(self._security_headers())
            return response
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    async def _accept_client(self, request: web.Request) -> web.StreamResponse:
        requested_protocols = {
            item.strip()
            for item in request.headers.get("Sec-WebSocket-Protocol", "").split(",")
        }
        if (
            not self._authorized(request)
            or request.headers.get("Origin") != self.origin
            or _SESSION_SUBPROTOCOL not in requested_protocols
            or (self._client_socket is not None and not self._client_socket.closed)
        ):
            raise web.HTTPForbidden()
        socket = web.WebSocketResponse(
            protocols=(_SESSION_SUBPROTOCOL,),
            heartbeat=20,
            max_msg_size=_MAX_CLIENT_MESSAGE_BYTES,
        )
        await socket.prepare(request)
        self._client_socket = socket
        registered = False
        try:
            first = await asyncio.wait_for(socket.receive(), timeout=10)
            registration = self._validate_registration(first)
            self.channel.router.register_endpoint(
                registration["endpointId"],
                registration["role"],
                registration["capabilities"],
                actor_id=registration["actorId"],
                actor_kind=registration["actorKind"],
            )
            registered = True
            self.client_registration_count += 1
            self._client_registered = True
            self.client_registered.set()
            await socket.send_json({"kind": "registered"})
            self._client_control_pump = asyncio.create_task(
                (
                    self._pump_client_control(socket)
                    if self.render_on == "server"
                    else self._pump_client_render(socket)
                ),
                name="molsysviewer-client-control",
            )
            if self._host is not None:
                self._host.send_worker_wire(
                    {
                        "kind": "peer-start",
                        "clientEndpointId": self.client_endpoint_id,
                        "actorId": self.client_actor_id,
                        "iceServers": list(self._ice_servers),
                    }
                )
            async for incoming in socket:
                if incoming.type is WSMsgType.TEXT:
                    await self._receive_client_json(incoming.json())
                elif incoming.type in {WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR}:
                    break
                else:
                    await socket.close(code=1003, message=b"unexpected binary frame")
                    break
        except Exception as error:
            self.last_client_error = str(error)
            await socket.close(code=1008, message=b"invalid session protocol")
        finally:
            if self._client_control_pump is not None:
                self._client_control_pump.cancel()
                await asyncio.gather(self._client_control_pump, return_exceptions=True)
                self._client_control_pump = None
            while not self._client_control_queue.empty():
                _, completion = self._client_control_queue.get_nowait()
                completion.cancel()
            while not self._client_render_queue.empty():
                self._client_render_queue.get_nowait()
            if registered:
                if self._host is not None:
                    self._host.send_worker_wire({"kind": "peer-stop"})
                self.channel.router.unregister_endpoint(self.client_endpoint_id)
            self._client_registered = False
            self.client_registered.clear()
            self.video_connected.clear()
            self.input_channel_open.clear()
            self.worker_input_received.clear()
            self.client_render_ready.clear()
            self.client_structure_complete.clear()
            if self._client_socket is socket:
                self._client_socket = None
        return socket

    def _validate_registration(self, message: Any) -> dict[str, Any]:
        if message.type is not WSMsgType.TEXT:
            raise ValueError("first client frame must be JSON")
        value = message.json()
        if not isinstance(value, Mapping):
            raise ValueError("client registration is malformed")
        capabilities = value.get("capabilities")
        if not isinstance(capabilities, Sequence) or isinstance(capabilities, (str, bytes)):
            raise ValueError("client registration capabilities are malformed")
        expected = {
            "kind": "register",
            "protocolVersion": 1,
            "viewerId": self.channel.router.viewer_id,
            "sessionId": self.channel.router.session_id,
            "endpointId": self.client_endpoint_id,
            "role": "browser-client",
            "actorId": self.client_actor_id,
            "actorKind": "human",
        }
        if any(value.get(key) != expected_value for key, expected_value in expected.items()):
            raise ValueError("client registration identity is invalid")
        expected_capabilities = (
            _SERVER_CLIENT_CAPABILITIES
            if self.render_on == "server"
            else _LOCAL_CLIENT_CAPABILITIES
        )
        if frozenset(capabilities) != expected_capabilities or len(capabilities) != len(
            expected_capabilities
        ):
            raise ValueError("client registration capabilities are invalid")
        return {**expected, "capabilities": tuple(capabilities)}

    async def _receive_client_json(self, value: Any) -> None:
        if not isinstance(value, Mapping):
            raise ValueError("client wire message is malformed")
        kind = value.get("kind")
        if kind == "signal":
            if self._host is None:
                raise ValueError("client rendering does not accept WebRTC signaling")
            validation = validate_signaling_packet(
                value.get("packet"),
                expected_viewer_id=self.channel.router.viewer_id,
                expected_session_id=self.channel.router.session_id,
                expected_endpoint_id=self.client_endpoint_id,
            )
            if validation.status != "accepted":
                raise ValueError(
                    f"client signaling rejected: {validation.reason}: {validation.detail}"
                )
            self._host.send_worker_wire({"kind": "signal", "packet": dict(value["packet"])})
            return
        if kind == "input":
            if self._host is None:
                raise ValueError("client rendering does not accept remote input packets")
            self._host.send_input(value.get("packet"))
            return
        if kind == "raw":
            if self._host is not None:
                raise ValueError("server-rendered clients may not originate raw data messages")
            result = self.channel.receive_data(
                value.get("message"), source_endpoint_id=self.client_endpoint_id
            )
            if result.status == "rejected":
                raise ValueError(
                    f"client data rejected: {result.reason}: {result.detail}"
                )
            message = value.get("message")
            event = message.get("event") if isinstance(message, Mapping) else None
            if event == "ready":
                self.client_render_ready.set()
            elif event == "structure_data_complete":
                self.client_structure_complete.set()
            return
        if kind == "control":
            pending_before = set(self._pending_client_control)
            result = self.channel.receive_control(value.get("envelope"))
            if result.status == "rejected":
                raise ValueError(
                    f"client control rejected: {result.reason}: {result.detail}"
                )
            produced = self._pending_client_control - pending_before
            if produced:
                await asyncio.gather(*produced)
            return
        if kind == "peer-state" and value.get("state") == "connected":
            self.video_connected.set()
            return
        if kind == "peer-state" and value.get("state") == "input-open":
            self.input_channel_open.set()
            return
        raise ValueError("client wire message kind is invalid")

    async def _forward_worker_signal(self, packet: Mapping[str, Any]) -> None:
        socket = self._client_socket
        if socket is None or socket.closed or not self._client_registered:
            raise RuntimeError("worker produced signaling without a registered client")
        await socket.send_json({"kind": "signal", "packet": dict(packet)})

    def _enqueue_client_render_control(self, envelope: Mapping[str, Any]) -> None:
        target = envelope.get("targetEndpointId")
        if target is not None and target != self.client_endpoint_id:
            return
        try:
            self._client_render_queue.put_nowait(
                ("control", {"kind": "control", "envelope": dict(envelope)})
            )
        except asyncio.QueueFull as error:
            raise RuntimeError("browser render outbound queue is full") from error

    def _enqueue_client_render_data(self, message: Mapping[str, Any], buffers: Any) -> None:
        target = message.get("target_endpoint_id")
        if target is not None and target != self.client_endpoint_id:
            return
        frozen_buffers = tuple(bytes(buffer) for buffer in (buffers or ()))
        header = {
            "kind": "data",
            "message": dict(message),
            "bufferCount": len(frozen_buffers),
            "byteLengths": [len(buffer) for buffer in frozen_buffers],
        }
        try:
            self._client_render_queue.put_nowait(("data", (header, frozen_buffers)))
        except asyncio.QueueFull as error:
            raise RuntimeError("browser render outbound queue is full") from error

    def _handle_worker_peer_state(self, value: Mapping[str, Any]) -> None:
        if value.get("state") == "input-received":
            self.worker_input_received.set()

    def _forward_client_control(self, envelope: Mapping[str, Any]) -> None:
        """Mirror projections addressed to the UI-only browser endpoint."""
        target = envelope.get("targetEndpointId")
        if target is not None and target != self.client_endpoint_id:
            return
        socket = self._client_socket
        if socket is None or socket.closed or not self._client_registered:
            return
        completion = asyncio.get_running_loop().create_future()
        self._pending_client_control.add(completion)
        completion.add_done_callback(self._pending_client_control.discard)
        try:
            self._client_control_queue.put_nowait((dict(envelope), completion))
        except asyncio.QueueFull as error:
            completion.cancel()
            raise RuntimeError("browser control outbound queue is full") from error

    async def _pump_client_control(
        self,
        socket: web.WebSocketResponse,
    ) -> None:
        try:
            while not socket.closed:
                envelope, completion = await self._client_control_queue.get()
                await socket.send_json({"kind": "control", "envelope": envelope})
                # aiohttp may complete a small send before its transport gets a
                # scheduling turn.  Yield once so a client that immediately
                # waits for the correlated answer cannot starve that flush.
                await asyncio.sleep(0)
                if not completion.done():
                    completion.set_result(None)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            for completion in tuple(self._pending_client_control):
                if not completion.done():
                    completion.set_exception(error)
            self.failure = f"browser control transport failed: {error}"
            if not socket.closed:
                await socket.close(code=1011, message=b"client control transport failed")

    async def _pump_client_render(self, socket: web.WebSocketResponse) -> None:
        try:
            while not socket.closed:
                kind, payload = await self._client_render_queue.get()
                if kind == "control":
                    await socket.send_json(payload)
                    continue
                header, buffers = payload
                await socket.send_json(header)
                for buffer in buffers:
                    await socket.send_bytes(buffer)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.failure = f"browser render transport failed: {error}"
            if not socket.closed:
                await socket.close(code=1011, message=b"client render transport failed")

    def _security_headers(self) -> dict[str, str]:
        return {
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
                f"connect-src 'self' ws://{self._listen_host}:{self._port}; "
                "img-src data: blob:; media-src blob:; font-src 'self' data:"
            ),
            "Cross-Origin-Resource-Policy": "same-origin",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        }


__all__ = ["RemoteSessionService"]
