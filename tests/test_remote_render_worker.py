"""RRS1 managed render-worker configuration and GPU policy guards."""

from __future__ import annotations

import asyncio
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest
from molsysviewer.remote import (
    ManagedRenderWorker,
    RenderWorkerConfig,
    find_chromium_executable,
    is_software_renderer,
)


@pytest.mark.parametrize(
    "renderer",
    [
        "ANGLE (Google, Vulkan 1.3 SwiftShader Device (Subzero))",
        "llvmpipe (LLVM 19.1.7, 256 bits)",
        "Mesa/X.org softpipe",
        "Software Rasterizer",
    ],
)
def test_software_renderers_are_identified(renderer):
    assert is_software_renderer(renderer)


@pytest.mark.parametrize(
    "renderer",
    [
        "ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1080, OpenGL 4.6)",
        "AMD Radeon RX 7900 XTX (radeonsi, navi31, LLVM 18.1.8)",
        "Apple M3",
    ],
)
def test_hardware_renderers_are_not_rejected(renderer):
    assert not is_software_renderer(renderer)


@pytest.mark.parametrize(
    ("update", "match"),
    [
        ({"gpu_policy": "auto"}, "gpu_policy"),
        ({"width": 0}, "width"),
        ({"height": True}, "height"),
        ({"frame_rate": 0}, "frame_rate"),
        ({"max_bitrate": -1}, "max_bitrate"),
        ({"startup_timeout": 0}, "startup_timeout"),
        ({"shutdown_timeout": False}, "shutdown_timeout"),
        ({"extra_arguments": ("",)}, "extra_arguments"),
        ({"extra_arguments": ("--remote-debugging-address=0.0.0.0",)}, "security"),
        ({"extra_arguments": ("--no-sandbox",)}, "security"),
    ],
)
def test_worker_configuration_rejects_implicit_or_unbounded_values(update, match):
    with pytest.raises(ValueError, match=match):
        RenderWorkerConfig(**update)


def test_chromium_resolution_accepts_an_explicit_executable(tmp_path):
    executable = tmp_path / "chrome"
    executable.touch()
    assert find_chromium_executable(str(executable)) == str(executable.resolve())


def test_worker_command_keeps_devtools_on_loopback_and_sandbox_enabled(tmp_path):
    executable = tmp_path / "chrome"
    executable.touch()
    worker = ManagedRenderWorker(RenderWorkerConfig(executable=str(executable)))

    command = worker._build_command(  # noqa: SLF001
        str(executable), tmp_path / "profile", "http://127.0.0.1:8000/worker"
    )

    assert "--remote-debugging-address=127.0.0.1" in command
    assert "--remote-debugging-port=0" in command
    assert "--use-angle=gl-egl" in command
    assert "--no-sandbox" not in command


def test_no_sandbox_is_only_an_explicit_visible_configuration(tmp_path):
    executable = tmp_path / "chrome"
    executable.touch()
    worker = ManagedRenderWorker(
        RenderWorkerConfig(executable=str(executable), no_sandbox=True)
    )
    command = worker._build_command(  # noqa: SLF001
        str(executable), tmp_path / "profile", "http://localhost:8000/worker"
    )
    assert "--no-sandbox" in command


@pytest.mark.skipif(
    os.environ.get("MSV_REAL_GPU_WORKER_TEST") != "1",
    reason="requires an explicitly selected real Chromium/GPU environment",
)
def test_real_worker_reports_hardware_webgl2_and_streaming_capabilities(tmp_path):
    (tmp_path / "worker.html").write_text(
        """
        <!doctype html>
        <meta charset="utf-8">
        <canvas id="render" width="1920" height="1080"></canvas>
        <script>
          const gl = document.querySelector('#render').getContext('webgl2');
          if (gl) {
            gl.clearColor(0.08, 0.12, 0.18, 1.0);
            gl.clear(gl.COLOR_BUFFER_BIT);
          }
        </script>
        """,
        encoding="utf-8",
    )
    handler = partial(SimpleHTTPRequestHandler, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    async def probe():
        worker = ManagedRenderWorker(
            RenderWorkerConfig(startup_timeout=20, shutdown_timeout=5)
        )
        try:
            diagnostics = await worker.start(
                f"http://127.0.0.1:{server.server_port}/worker.html"
            )
            assert worker.state == "ready"
            assert worker.is_running
            assert diagnostics.webgl2
            assert diagnostics.webrtc
            assert diagnostics.capture_stream
            assert not diagnostics.software_rendering
            assert diagnostics.renderer
            first_pid = diagnostics.pid

            restarted = await worker.restart()
            assert restarted.pid != first_pid
            assert worker.state == "ready"
            with pytest.raises(RuntimeError, match="restart has already been used"):
                await worker.restart()

            process = worker._process  # noqa: SLF001
            assert process is not None
            process.terminate()
            await process.wait()
            assert await worker.refresh_state() == "failed"
            assert "exited unexpectedly" in (worker.failure or "")
        finally:
            await worker.close()
        assert worker.state == "stopped"
        assert not worker.is_running

    try:
        asyncio.run(probe())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
