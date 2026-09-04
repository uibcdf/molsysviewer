"""Private loopback host connecting a managed render worker to one session.

This is an implementation transport, not the future public remote-session API.
The browser page and WebSocket stay on loopback; the session router remains the
authority for every message that crosses the internal connection.
"""

from __future__ import annotations

import asyncio
import hmac
import inspect
import secrets
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from aiohttp import WSMsgType, web

from .protocol import validate_input_packet, validate_signaling_packet
from .render_worker import ManagedRenderWorker, RenderWorkerConfig, RenderWorkerDiagnostics
from .view_channel import RemoteViewChannel

_INTERNAL_SUBPROTOCOL = "molsysviewer-internal-v1"
_WORKER_CAPABILITIES = frozenset(
    {"input-receive", "render", "structure-receive", "video-send"}
)
_VIEWER_JS = Path(__file__).resolve().parents[1] / "viewer.js"

_WORKER_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MolSysViewer render worker</title>
  <style>
    html, body, #molsysviewer-worker { width: 100%; height: 100%; margin: 0; overflow: hidden; }
    body { background: #080b10; }
  </style>
</head>
<body>
  <div id="molsysviewer-worker"></div>
  <script type="module" src="/internal/worker-bootstrap.js"></script>
</body>
</html>
"""

_WORKER_BOOTSTRAP = """import { bootRenderWorker } from './viewer.js';

const response = await fetch('./config', { credentials: 'same-origin', cache: 'no-store' });
if (!response.ok) throw new Error(`render-worker config failed: ${response.status}`);
const config = await response.json();
const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
const runtime = await bootRenderWorker({
    el: document.querySelector('#molsysviewer-worker'),
    websocketUrl: `${scheme}//${location.host}/internal/ws`,
    viewerId: config.viewerId,
    sessionId: config.sessionId,
    endpointId: config.endpointId,
    width: config.width,
    height: config.height,
    frameRate: config.frameRate,
    maxBitrate: config.maxBitrate,
});
globalThis.__molsysviewerRenderWorker = runtime;
"""


class InternalRenderWorkerHost:
    """Own the loopback HTTP/WS seam and one managed Chromium worker."""

    def __init__(
        self,
        worker_config: RenderWorkerConfig | None = None,
        *,
        queue_capacity: int = 256,
    ) -> None:
        if not isinstance(queue_capacity, int) or isinstance(queue_capacity, bool) or queue_capacity < 1:
            raise ValueError("queue_capacity must be a positive integer")
        self._queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue(queue_capacity)
        self.channel = RemoteViewChannel(
            self._enqueue_control,
            render_on="server",
            send_data=self._enqueue_data,
        )
        self.worker = ManagedRenderWorker(worker_config)
        self.frontend_ready = asyncio.Event()
        self.structure_complete = asyncio.Event()
        self.worker_connected = asyncio.Event()
        self._token = secrets.token_urlsafe(32)
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None
        self._socket: web.WebSocketResponse | None = None
        self._pump_task: asyncio.Task[None] | None = None
        self._host = "127.0.0.1"
        self._port: int | None = None
        self._closed = False
        self.failure: str | None = None
        self.last_structure_error: str | None = None
        self.worker_signal_sink: Any = None
        self.worker_peer_state_sink: Any = None
        # Optional observer owned by the public session service.  Control
        # projections still follow their normal worker route; the observer lets
        # a UI-only client receive the same canonical Python projection without
        # making this private host aware of browser sockets.
        self.client_control_sink: Any = None

    @property
    def endpoint_id(self) -> str:
        return f"render-worker:{self.channel.router.session_id}"

    @property
    def origin(self) -> str:
        if self._port is None:
            raise RuntimeError("internal render-worker host has not started")
        return f"http://{self._host}:{self._port}"

    @property
    def worker_url(self) -> str:
        return f"{self.origin}/internal/worker"

    async def start(self) -> str:
        """Start the authenticated loopback service without launching Chromium."""
        if self._closed:
            raise RuntimeError("internal render-worker host is closed")
        if self._runner is not None:
            return self.worker_url
        _ = self.channel.router  # fail before opening a socket if no MolSysView is bound
        app = web.Application(client_max_size=64 * 1024 * 1024)
        app.add_routes(
            [
                web.get("/internal/worker", self._serve_worker),
                web.get("/internal/worker-bootstrap.js", self._serve_bootstrap),
                web.get("/internal/viewer.js", self._serve_viewer),
                web.get("/internal/config", self._serve_config),
                web.get("/internal/ws", self._accept_socket),
            ]
        )
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        site = web.TCPSite(runner, self._host, 0)
        try:
            await site.start()
            sockets = getattr(site._server, "sockets", None)  # noqa: SLF001
            if not sockets:
                raise RuntimeError("loopback render-worker service did not bind a socket")
            self._port = int(sockets[0].getsockname()[1])
        except BaseException:
            await runner.cleanup()
            raise
        self._runner = runner
        self._site = site
        return self.worker_url

    async def launch_worker(self) -> RenderWorkerDiagnostics:
        """Launch Chromium and wait until its MolSysViewer runtime says ``ready``."""
        if self._runner is None:
            await self.start()
        self.frontend_ready.clear()
        self.structure_complete.clear()
        self.failure = None
        self.last_structure_error = None
        diagnostics = await self.worker.start(self.worker_url)
        try:
            await asyncio.wait_for(
                self.frontend_ready.wait(), timeout=self.worker.config.startup_timeout
            )
        except TimeoutError as error:
            await self.worker.close()
            detail = self.failure or "the internal worker sent no accepted ready event"
            raise TimeoutError(f"render-worker session handshake timed out: {detail}") from error
        except BaseException:
            await self.worker.close()
            raise
        return diagnostics

    async def restart_worker(self) -> RenderWorkerDiagnostics:
        """Consume the managed worker's bounded restart and await its new runtime."""
        if self._closed:
            raise RuntimeError("internal render-worker host is closed")
        socket = self._socket
        if socket is not None:
            if not socket.closed:
                await socket.close(code=1012, message=b"worker restarting")
            deadline = asyncio.get_running_loop().time() + self.worker.config.shutdown_timeout
            while self._socket is socket and asyncio.get_running_loop().time() < deadline:
                await asyncio.sleep(0.01)
            if self._socket is socket:
                raise TimeoutError("render-worker socket did not detach before restart")
        while not self._queue.empty():
            self._queue.get_nowait()
        self.frontend_ready.clear()
        self.structure_complete.clear()
        self.worker_connected.clear()
        self.failure = None
        self.last_structure_error = None
        diagnostics = await self.worker.restart()
        try:
            await asyncio.wait_for(
                self.frontend_ready.wait(), timeout=self.worker.config.startup_timeout
            )
        except BaseException:
            await self.worker.close()
            raise
        return diagnostics

    async def wait_for_structure(self, timeout: float = 30.0) -> None:
        try:
            await asyncio.wait_for(self.structure_complete.wait(), timeout=timeout)
        except TimeoutError as error:
            detail = self.last_structure_error or self.failure or "no terminal structure event"
            raise TimeoutError(f"render-worker structure transfer timed out: {detail}") from error

    def send_input(self, packet: Mapping[str, Any]) -> None:
        """Forward input only for a registered human client in this session."""
        validation = validate_input_packet(
            packet,
            expected_viewer_id=self.channel.router.viewer_id,
            expected_session_id=self.channel.router.session_id,
        )
        if validation.status != "accepted" or validation.packet is None:
            raise ValueError(
                f"remote input rejected: {validation.reason}: {validation.detail}"
            )
        source = self.channel.router.endpoint(validation.packet.endpoint_id)
        if (
            source is None
            or source.role not in {"browser-client", "qt-client"}
            or source.actor_kind != "human"
            or "input-send" not in source.capabilities
        ):
            raise ValueError("remote input source is not a registered human client")
        self._enqueue(("input", {"kind": "input", "packet": dict(packet)}))

    def send_worker_wire(self, value: Mapping[str, Any]) -> None:
        """Send one session-service wire message to the authenticated worker."""
        self._enqueue(("wire", dict(value)))

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self.worker.close()
        socket = self._socket
        if socket is not None and not socket.closed:
            await socket.close(code=1001, message=b"host closed")
        if self._pump_task is not None:
            self._pump_task.cancel()
            await asyncio.gather(self._pump_task, return_exceptions=True)
            self._pump_task = None
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._site = None
            self._port = None
        self.channel.close()

    def _enqueue_control(self, envelope: Mapping[str, Any]) -> None:
        target = envelope.get("targetEndpointId")
        if target is None or target == self.endpoint_id:
            self._enqueue(("control", {"kind": "control", "envelope": dict(envelope)}))
        sink = self.client_control_sink
        if sink is not None:
            sink(dict(envelope))

    def _enqueue_data(self, message: Mapping[str, Any], buffers: Any) -> None:
        target = message.get("target_endpoint_id")
        if target is not None and target != self.endpoint_id:
            return
        frozen_buffers = tuple(bytes(buffer) for buffer in (buffers or ()))
        header = {
            "kind": "data",
            "message": dict(message),
            "bufferCount": len(frozen_buffers),
            "byteLengths": [len(buffer) for buffer in frozen_buffers],
        }
        self._enqueue(("data", (header, frozen_buffers)))

    def _enqueue(self, item: tuple[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("internal render-worker host is closed")
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull as error:
            raise RuntimeError("internal render-worker outbound queue is full") from error

    def _authorized(self, request: web.Request) -> bool:
        supplied = request.cookies.get("molsysviewer_worker_token", "")
        return bool(supplied) and hmac.compare_digest(supplied, self._token)

    async def _serve_worker(self, request: web.Request) -> web.Response:
        response = web.Response(text=_WORKER_HTML, content_type="text/html")
        response.set_cookie(
            "molsysviewer_worker_token",
            self._token,
            httponly=True,
            samesite="Strict",
            path="/internal",
        )
        response.headers.update(self._security_headers())
        return response

    async def _serve_bootstrap(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPForbidden()
        response = web.Response(text=_WORKER_BOOTSTRAP, content_type="text/javascript")
        response.headers.update(self._security_headers())
        return response

    async def _serve_viewer(self, request: web.Request) -> web.StreamResponse:
        if not self._authorized(request):
            raise web.HTTPForbidden()
        response = web.FileResponse(_VIEWER_JS)
        response.content_type = "text/javascript"
        response.headers.update(self._security_headers())
        return response

    async def _serve_config(self, request: web.Request) -> web.Response:
        if not self._authorized(request):
            raise web.HTTPForbidden()
        response = web.json_response(
            {
                "viewerId": self.channel.router.viewer_id,
                "sessionId": self.channel.router.session_id,
                "endpointId": self.endpoint_id,
                "width": self.worker.config.width,
                "height": self.worker.config.height,
                "frameRate": self.worker.config.frame_rate,
                "maxBitrate": self.worker.config.max_bitrate,
            }
        )
        response.headers.update(self._security_headers())
        return response

    async def _accept_socket(self, request: web.Request) -> web.StreamResponse:
        if (
            not self._authorized(request)
            or request.headers.get("Origin") != self.origin
            or _INTERNAL_SUBPROTOCOL
            not in {
                item.strip()
                for item in request.headers.get("Sec-WebSocket-Protocol", "").split(",")
            }
            or (self._socket is not None and not self._socket.closed)
        ):
            raise web.HTTPForbidden()
        socket = web.WebSocketResponse(
            protocols=(_INTERNAL_SUBPROTOCOL,),
            heartbeat=20,
            max_msg_size=36 * 1024 * 1024,
        )
        await socket.prepare(request)
        self._socket = socket
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
            self.worker_connected.set()
            await socket.send_json({"kind": "registered"})
            self._pump_task = asyncio.create_task(self._pump_outbound(socket))
            async for incoming in socket:
                if incoming.type is WSMsgType.TEXT:
                    await self._receive_json(incoming.json())
                elif incoming.type in {WSMsgType.CLOSE, WSMsgType.CLOSED, WSMsgType.ERROR}:
                    break
                else:
                    await socket.close(code=1003, message=b"unexpected binary frame")
                    break
        except Exception as error:
            self.failure = str(error)
            await socket.close(code=1008, message=b"invalid worker protocol")
        finally:
            if self._pump_task is not None:
                self._pump_task.cancel()
                await asyncio.gather(self._pump_task, return_exceptions=True)
                self._pump_task = None
            if registered:
                self.channel.router.unregister_endpoint(self.endpoint_id)
            self.worker_connected.clear()
            if self._socket is socket:
                self._socket = None
        return socket

    def _validate_registration(self, message: Any) -> dict[str, Any]:
        if message.type is not WSMsgType.TEXT:
            raise ValueError("first worker frame must be JSON")
        value = message.json()
        if not isinstance(value, Mapping):
            raise ValueError("worker registration is malformed")
        capabilities = value.get("capabilities")
        if not isinstance(capabilities, Sequence) or isinstance(capabilities, (str, bytes)):
            raise ValueError("worker registration capabilities are malformed")
        expected = {
            "kind": "register",
            "protocolVersion": 1,
            "viewerId": self.channel.router.viewer_id,
            "sessionId": self.channel.router.session_id,
            "endpointId": self.endpoint_id,
            "role": "render-worker",
            "actorId": self.endpoint_id,
            "actorKind": "system",
        }
        if any(value.get(key) != expected_value for key, expected_value in expected.items()):
            raise ValueError("worker registration identity is invalid")
        if frozenset(capabilities) != _WORKER_CAPABILITIES or len(capabilities) != len(
            _WORKER_CAPABILITIES
        ):
            raise ValueError("worker registration capabilities are invalid")
        return {**expected, "capabilities": tuple(capabilities)}

    async def _receive_json(self, value: Any) -> None:
        if not isinstance(value, Mapping):
            raise ValueError("worker wire message is malformed")
        kind = value.get("kind")
        if kind == "control":
            result = self.channel.receive_control(value.get("envelope"))
        elif kind == "raw":
            result = self.channel.receive_data(
                value.get("message"), source_endpoint_id=self.endpoint_id
            )
            message = value.get("message")
            event = message.get("event") if isinstance(message, Mapping) else None
            if result.status == "accepted" and event == "ready":
                self.frontend_ready.set()
            elif result.status == "accepted" and event == "structure_data_complete":
                self.structure_complete.set()
            elif result.status == "accepted" and event == "structure_data_error":
                self.last_structure_error = str(message.get("error") or "unknown structure error")
        elif kind == "signal":
            validation = validate_signaling_packet(
                value.get("packet"),
                expected_viewer_id=self.channel.router.viewer_id,
                expected_session_id=self.channel.router.session_id,
                expected_endpoint_id=self.endpoint_id,
            )
            if validation.status != "accepted":
                raise ValueError(
                    f"worker signaling rejected: {validation.reason}: {validation.detail}"
                )
            sink = self.worker_signal_sink
            if sink is not None:
                outcome = sink(dict(value["packet"]))
                if inspect.isawaitable(outcome):
                    await outcome
            return
        elif kind == "peer-state":
            if value.get("state") != "input-received":
                raise ValueError("worker peer state is invalid")
            sequence = value.get("sequence")
            if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
                raise ValueError("worker peer input sequence is invalid")
            sink = self.worker_peer_state_sink
            if sink is not None:
                outcome = sink(dict(value))
                if inspect.isawaitable(outcome):
                    await outcome
            return
        else:
            raise ValueError("worker wire message kind is invalid")
        if result.status == "rejected":
            raise ValueError(
                f"worker message rejected: {result.reason}: {result.detail}"
            )

    async def _pump_outbound(self, socket: web.WebSocketResponse) -> None:
        try:
            while not socket.closed:
                kind, payload = await self._queue.get()
                if kind in {"control", "input", "wire"}:
                    await socket.send_json(payload)
                    continue
                header, buffers = payload
                await socket.send_json(header)
                for buffer in buffers:
                    await socket.send_bytes(buffer)
        except asyncio.CancelledError:
            raise
        except Exception as error:
            self.failure = f"render-worker outbound transport failed: {error}"
            await socket.close(code=1011, message=b"worker transport failed")

    def _security_headers(self) -> dict[str, str]:
        return {
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
                f"connect-src 'self' ws://{self._host}:{self._port}; "
                "img-src data: blob:; font-src 'self' data:; worker-src 'self' blob:; "
                "media-src blob:"
            ),
            "Cross-Origin-Resource-Policy": "same-origin",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        }


__all__ = ["InternalRenderWorkerHost"]
