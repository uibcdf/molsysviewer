"""Managed Chromium lifecycle for server-side rendering.

The worker owns a Chromium process and its ephemeral profile.  DevTools is a
loopback-only implementation channel used for health checks; it is never the
remote-client protocol and is not exposed by this module.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping
from urllib.parse import urlparse

GpuPolicy = Literal["require-hardware", "allow-software"]
WorkerState = Literal["new", "starting", "ready", "failed", "stopped"]
_RESERVED_ARGUMENTS = frozenset(
    {
        "--no-sandbox",
        "--remote-debugging-address",
        "--remote-debugging-port",
        "--user-data-dir",
    }
)


def _positive_integer(name: str, value: Any) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True)
class RenderWorkerConfig:
    executable: str | None = None
    gpu_policy: GpuPolicy = "require-hardware"
    width: int = 1920
    height: int = 1080
    frame_rate: int = 30
    max_bitrate: int = 8_000_000
    startup_timeout: float = 15.0
    shutdown_timeout: float = 5.0
    no_sandbox: bool = False
    extra_arguments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.gpu_policy not in {"require-hardware", "allow-software"}:
            raise ValueError("gpu_policy must be 'require-hardware' or 'allow-software'")
        for name in ("width", "height", "frame_rate", "max_bitrate"):
            _positive_integer(name, getattr(self, name))
        for name in ("startup_timeout", "shutdown_timeout"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                raise ValueError(f"{name} must be positive")
        if isinstance(self.extra_arguments, (str, bytes)) or any(
            not isinstance(item, str) or not item for item in self.extra_arguments
        ):
            raise ValueError("extra_arguments must contain non-empty strings")
        overridden = sorted(
            item
            for item in self.extra_arguments
            if item.split("=", 1)[0] in _RESERVED_ARGUMENTS
        )
        if overridden:
            raise ValueError(
                f"extra_arguments may not override managed security arguments: {overridden}"
            )


@dataclass(frozen=True)
class RenderWorkerDiagnostics:
    pid: int
    product: str
    webgl2: bool
    renderer: str
    software_rendering: bool
    webrtc: bool
    capture_stream: bool
    gpu_feature_status: Mapping[str, Any]


def find_chromium_executable(explicit: str | None = None) -> str:
    """Resolve a Chromium-family executable without shell invocation."""
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_file():
            raise FileNotFoundError(f"Chromium executable does not exist: {candidate}")
        return str(candidate.resolve())
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        candidate = shutil.which(name)
        if candidate:
            return candidate
    raise FileNotFoundError(
        "No Chromium-family executable was found; configure RenderWorkerConfig.executable"
    )


def is_software_renderer(renderer: str) -> bool:
    normalized = renderer.casefold()
    return any(
        marker in normalized
        for marker in ("swiftshader", "llvmpipe", "softpipe", "software rasterizer")
    )


def _validate_worker_url(worker_url: str) -> None:
    parsed = urlparse(worker_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("worker_url must use HTTP or HTTPS")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("worker_url must be served on loopback")


class ManagedRenderWorker:
    """Launch, diagnose, stop and restart one headless Chromium worker."""

    def __init__(self, config: RenderWorkerConfig | None = None) -> None:
        self.config = config or RenderWorkerConfig()
        self.state: WorkerState = "new"
        self.diagnostics: RenderWorkerDiagnostics | None = None
        self.failure: str | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._profile: tempfile.TemporaryDirectory[str] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._stderr_tail: deque[str] = deque(maxlen=80)
        self._restart_count = 0
        self._worker_url: str | None = None
        self._page_websocket_url: str | None = None

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    @property
    def stderr_tail(self) -> tuple[str, ...]:
        return tuple(self._stderr_tail)

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.returncode is None

    async def start(self, worker_url: str) -> RenderWorkerDiagnostics:
        if self.state not in {"new", "stopped"}:
            raise RuntimeError(f"worker cannot start from state {self.state}")
        _validate_worker_url(worker_url)
        executable = find_chromium_executable(self.config.executable)
        self.state = "starting"
        self.failure = None
        self.diagnostics = None
        self._worker_url = worker_url
        self._profile = tempfile.TemporaryDirectory(prefix="molsysviewer-render-worker-")
        profile_path = Path(self._profile.name)
        command = self._build_command(executable, profile_path, worker_url)
        try:
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            self._stderr_task = asyncio.create_task(self._collect_stderr())
            port, browser_path = await self._wait_for_devtools(profile_path)
            diagnostics = await self._diagnose(port, browser_path)
            if not diagnostics.webgl2:
                raise RuntimeError(
                    "render worker did not provide WebGL2: its page loaded but no canvas "
                    "yielded a webgl2 context"
                )
            if not diagnostics.webrtc or not diagnostics.capture_stream:
                raise RuntimeError("render worker lacks WebRTC canvas streaming capabilities")
            if self.config.gpu_policy == "require-hardware" and diagnostics.software_rendering:
                raise RuntimeError(
                    f"software renderer rejected by GPU policy: {diagnostics.renderer}"
                )
            self.diagnostics = diagnostics
            self.state = "ready"
            return diagnostics
        except BaseException as error:
            self.failure = str(error)
            self.state = "failed"
            await self._terminate(preserve_state=True)
            raise

    async def refresh_state(self) -> WorkerState:
        if self.state == "ready" and not self.is_running:
            self.failure = f"Chromium exited unexpectedly with code {self._process.returncode}"
            self.state = "failed"
        return self.state

    async def peer_diagnostics(self) -> Mapping[str, Any]:
        """Read WebRTC sender diagnostics from the private worker page."""
        websocket_url = self._page_websocket_url
        if websocket_url is None or not self.is_running:
            return {"worker": "unavailable"}
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=self.config.startup_timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            response = await self._cdp_call(
                session,
                websocket_url,
                "Runtime.evaluate",
                {
                    "expression": "globalThis.__molsysviewerRenderWorker?.peerDiagnostics?.()",
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            )
        result = response.get("result", {})
        value = result.get("value")
        return dict(value) if isinstance(value, Mapping) else {"worker": "malformed"}

    async def restart(self) -> RenderWorkerDiagnostics:
        if self._restart_count >= 1:
            raise RuntimeError("the bounded render-worker restart has already been used")
        if self._worker_url is None:
            raise RuntimeError("worker has not been started")
        worker_url = self._worker_url
        self._restart_count += 1
        await self.close()
        return await self.start(worker_url)

    async def close(self) -> None:
        await self._terminate(preserve_state=False)

    def _build_command(self, executable: str, profile_path: Path, worker_url: str) -> tuple[str, ...]:
        arguments = [
            executable,
            "--headless=new",
            "--use-gl=angle",
            "--use-angle=gl-egl",
            "--remote-debugging-address=127.0.0.1",
            "--remote-debugging-port=0",
            f"--user-data-dir={profile_path}",
            f"--window-size={self.config.width},{self.config.height}",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-background-networking",
        ]
        if self.config.no_sandbox:
            arguments.append("--no-sandbox")
        arguments.extend(self.config.extra_arguments)
        arguments.append(worker_url)
        return tuple(arguments)

    async def _collect_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        while line := await process.stderr.readline():
            self._stderr_tail.append(line.decode("utf-8", errors="replace").rstrip())

    async def _wait_for_devtools(self, profile_path: Path) -> tuple[int, str]:
        active_port = profile_path / "DevToolsActivePort"
        deadline = asyncio.get_running_loop().time() + self.config.startup_timeout
        while asyncio.get_running_loop().time() < deadline:
            if self._process is not None and self._process.returncode is not None:
                raise RuntimeError(f"Chromium exited during startup with code {self._process.returncode}")
            try:
                lines = active_port.read_text(encoding="utf-8").splitlines()
            except (FileNotFoundError, OSError):
                lines = []
            if len(lines) >= 2 and lines[0].isdigit() and lines[1].startswith("/devtools/browser/"):
                return int(lines[0]), lines[1]
            await asyncio.sleep(0.05)
        raise TimeoutError("Chromium did not expose its loopback DevTools endpoint in time")

    async def _diagnose(self, port: int, browser_path: str) -> RenderWorkerDiagnostics:
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=self.config.startup_timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"http://127.0.0.1:{port}/json/version") as response:
                response.raise_for_status()
                version = await response.json()
            target = await self._wait_for_page_target(session, port)
            self._page_websocket_url = str(target["webSocketDebuggerUrl"])
            gpu = await self._cdp_call(
                session,
                f"ws://127.0.0.1:{port}{browser_path}",
                "SystemInfo.getInfo",
            )
            page = await self._cdp_call(
                session,
                target["webSocketDebuggerUrl"],
                "Runtime.evaluate",
                {
                    "expression": _DIAGNOSTIC_EXPRESSION,
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            )
        result = page.get("result", {})
        if "exceptionDetails" in page or "value" not in result:
            raise RuntimeError("worker page diagnostics could not be evaluated")
        value = result["value"]
        if not isinstance(value, Mapping):
            raise RuntimeError("worker page returned malformed diagnostics")
        # A page that never committed its navigation reports `about:blank` here while the
        # DevTools target still advertises the URL it was asked for, so `/json/list` looks
        # correct and the document is empty. Distinguishing the two matters: "no WebGL2"
        # sends the reader to drivers and GPUs, and the cause is that nothing was loaded.
        document_url = str(value.get("documentUrl") or "")
        if document_url == "about:blank" and self._worker_url != "about:blank":
            raise RuntimeError(
                f"the render worker page never loaded: the browser was asked for "
                f"{self._worker_url} and its document is still about:blank. The DevTools "
                f"target advertises the requested URL either way, so this is not a missing "
                f"page target. A browser that cannot complete a command-line navigation to "
                f"http on this host produces exactly this "
                f"(see uibcdf/molsysviewer#77)."
            )
        renderer = str(value.get("renderer") or gpu.get("gpu", {}).get("auxAttributes", {}).get("glRenderer") or "")
        if not renderer:
            raise RuntimeError("worker did not report its WebGL renderer")
        return RenderWorkerDiagnostics(
            pid=self._process.pid,  # type: ignore[union-attr]
            product=str(version.get("Browser", "unknown")),
            webgl2=value.get("webgl2") is True,
            renderer=renderer,
            software_rendering=is_software_renderer(renderer),
            webrtc=value.get("webrtc") is True,
            capture_stream=value.get("captureStream") is True,
            gpu_feature_status=dict(gpu.get("gpu", {}).get("featureStatus", {})),
        )

    async def _wait_for_page_target(self, session: Any, port: int) -> Mapping[str, Any]:
        deadline = asyncio.get_running_loop().time() + self.config.startup_timeout
        while asyncio.get_running_loop().time() < deadline:
            async with session.get(f"http://127.0.0.1:{port}/json/list") as response:
                response.raise_for_status()
                targets = await response.json()
            for target in targets:
                if target.get("type") == "page" and target.get("url") == self._worker_url:
                    return target
            await asyncio.sleep(0.05)
        raise TimeoutError("Chromium did not create the render-worker page target in time")

    @staticmethod
    async def _cdp_call(
        session: Any,
        websocket_url: str,
        method: str,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        async with session.ws_connect(websocket_url, max_msg_size=4 * 1024 * 1024) as socket:
            await socket.send_json({"id": 1, "method": method, "params": dict(params or {})})
            async for message in socket:
                if message.type.name == "TEXT":
                    value = message.json()
                    if value.get("id") != 1:
                        continue
                    if "error" in value:
                        raise RuntimeError(f"CDP {method} failed: {value['error']}")
                    return value.get("result", {})
                if message.type.name in {"CLOSE", "CLOSED", "ERROR"}:
                    break
        raise RuntimeError(f"CDP {method} connection closed without a response")

    async def _terminate(self, *, preserve_state: bool) -> None:
        process = self._process
        if process is not None and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=self.config.shutdown_timeout)
            except TimeoutError:
                process.kill()
                await process.wait()
        if self._stderr_task is not None:
            await asyncio.gather(self._stderr_task, return_exceptions=True)
        self._stderr_task = None
        self._process = None
        self._page_websocket_url = None
        if self._profile is not None:
            self._profile.cleanup()
            self._profile = None
        self.diagnostics = None if not preserve_state else self.diagnostics
        if not preserve_state:
            self.state = "stopped"


_DIAGNOSTIC_EXPRESSION = """
(async () => {
  const deadline = performance.now() + 10000;
  let canvas = null;
  let gl = null;
  while (performance.now() < deadline) {
    canvas = [...document.querySelectorAll('canvas')]
      .sort((a, b) => b.width * b.height - a.width * a.height)[0] || null;
    gl = canvas ? canvas.getContext('webgl2') : null;
    if (gl) break;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  const extension = gl ? gl.getExtension('WEBGL_debug_renderer_info') : null;
  return {
    documentUrl: String(location.href),
    canvasCount: document.querySelectorAll('canvas').length,
    webgl2: !!gl,
    renderer: gl ? String(gl.getParameter(extension ? extension.UNMASKED_RENDERER_WEBGL : gl.RENDERER)) : '',
    webrtc: typeof RTCPeerConnection === 'function',
    captureStream: !!canvas && typeof canvas.captureStream === 'function',
  };
})()
"""


__all__ = [
    "ManagedRenderWorker",
    "RenderWorkerConfig",
    "RenderWorkerDiagnostics",
    "find_chromium_executable",
    "is_software_renderer",
]
