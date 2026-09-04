"""Real loopback tests for the private render-worker transport."""

from __future__ import annotations

import asyncio
import os
import re
from types import SimpleNamespace

import aiohttp
import pytest
from molsysviewer.demo import demo
from molsysviewer.remote import InternalRenderWorkerHost, RenderWorkerConfig
from molsysviewer.viewer import MolSysView


def test_restart_accepts_a_worker_socket_that_already_detached():
    class FakeWorker:
        def __init__(self, host):
            self.host = host
            self.config = SimpleNamespace(shutdown_timeout=0.1, startup_timeout=0.1)

        async def restart(self):
            self.host.frontend_ready.set()
            return SimpleNamespace(pid=2)

        async def close(self):
            return None

    async def probe() -> None:
        host = InternalRenderWorkerHost()
        view = MolSysView(transport=host.channel)
        host.worker = FakeWorker(host)
        try:
            diagnostics = await host.restart_worker()
            assert diagnostics.pid == 2
        finally:
            await host.close()
            view.close()

    asyncio.run(probe())


def test_internal_host_authenticates_registration_and_preserves_binary_frames():
    async def probe() -> None:
        host = InternalRenderWorkerHost()
        view = MolSysView(transport=host.channel)
        try:
            worker_url = await host.start()
            assert worker_url.endswith("/internal/worker")
            assert "?" not in worker_url

            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                async with session.get(f"{host.origin}/internal/config") as response:
                    assert response.status == 403
                async with session.get(worker_url) as response:
                    assert response.status == 200
                    assert "molsysviewer_worker_token" not in await response.text()
                    cookie = response.cookies["molsysviewer_worker_token"]
                    assert cookie["httponly"] is True
                    assert cookie["samesite"] == "Strict"
                async with session.get(f"{host.origin}/internal/config") as response:
                    config = await response.json()

                async with session.ws_connect(
                    f"{host.origin}/internal/ws",
                    origin=host.origin,
                    protocols=("molsysviewer-internal-v1",),
                ) as socket:
                    await socket.send_json(
                        {
                            "kind": "register",
                            "protocolVersion": 1,
                            "viewerId": config["viewerId"],
                            "sessionId": config["sessionId"],
                            "endpointId": config["endpointId"],
                            "role": "render-worker",
                            "actorId": config["endpointId"],
                            "actorKind": "system",
                            "capabilities": [
                                "input-receive",
                                "render",
                                "structure-receive",
                                "video-send",
                            ],
                        }
                    )
                    registered = await socket.receive_json(timeout=2)
                    assert registered == {"kind": "registered"}
                    assert host.channel.router.endpoint(host.endpoint_id) is not None

                    host.channel.send(
                        {
                            "op": "structure_data_chunk",
                            "protocol_version": 1,
                            "generation": 1,
                        },
                        buffers=[memoryview(b"coordinates"), memoryview(b"time")],
                    )
                    header = await socket.receive_json(timeout=2)
                    assert header["kind"] == "data"
                    assert header["bufferCount"] == 2
                    assert header["byteLengths"] == [11, 4]
                    assert (await socket.receive(timeout=2)).data == b"coordinates"
                    assert (await socket.receive(timeout=2)).data == b"time"

                    client_endpoint = "browser-client:test"
                    host.channel.router.register_endpoint(
                        client_endpoint,
                        "browser-client",
                        {"command-origin", "input-send", "video-receive", "workbench"},
                        actor_id="human:test",
                        actor_kind="human",
                    )
                    input_packet = {
                        "protocolVersion": 1,
                        "viewerId": config["viewerId"],
                        "sessionId": config["sessionId"],
                        "endpointId": client_endpoint,
                        "sequence": 1,
                        "timestampMs": 1.0,
                        "kind": "pointer",
                        "viewport": {
                            "width": 800,
                            "height": 600,
                            "devicePixelRatio": 1,
                        },
                        "payload": {
                            "phase": "move",
                            "pointerType": "mouse",
                            "pointerId": 1,
                            "x": 0.5,
                            "y": 0.5,
                            "button": -1,
                            "buttons": 0,
                            "modifiers": {},
                        },
                    }
                    host.send_input(input_packet)
                    assert await socket.receive_json(timeout=2) == {
                        "kind": "input",
                        "packet": input_packet,
                    }

                    await socket.send_json(
                        {
                            "kind": "raw",
                            "message": {
                                "event": "ready",
                                "capabilities": {"binary_structure_data": [1]},
                            },
                        }
                    )
                    await asyncio.wait_for(host.frontend_ready.wait(), timeout=2)
                    assert view._ready is True  # noqa: SLF001
        finally:
            await host.close()
            view.close()

    asyncio.run(probe())


def test_internal_host_rejects_a_worker_with_the_wrong_session_identity():
    async def probe() -> None:
        host = InternalRenderWorkerHost()
        view = MolSysView(transport=host.channel)
        try:
            worker_url = await host.start()
            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                async with session.get(worker_url):
                    pass
                async with session.ws_connect(
                    f"{host.origin}/internal/ws",
                    origin=host.origin,
                    protocols=("molsysviewer-internal-v1",),
                ) as socket:
                    await socket.send_json(
                        {
                            "kind": "register",
                            "protocolVersion": 1,
                            "viewerId": host.channel.router.viewer_id,
                            "sessionId": "wrong-session",
                            "endpointId": host.endpoint_id,
                            "role": "render-worker",
                            "actorId": host.endpoint_id,
                            "actorKind": "system",
                            "capabilities": sorted(
                                {
                                    "input-receive",
                                    "render",
                                    "structure-receive",
                                    "video-send",
                                }
                            ),
                        }
                    )
                    message = await socket.receive(timeout=2)
                    assert message.type is aiohttp.WSMsgType.CLOSE
                    assert message.data == 1008
            assert host.channel.router.endpoint(host.endpoint_id) is None
        finally:
            await host.close()
            view.close()

    asyncio.run(probe())


@pytest.mark.skipif(
    os.environ.get("MSV_REAL_GPU_WORKER_TEST") != "1",
    reason="requires an explicitly selected real Chromium/GPU environment",
)
def test_real_worker_loads_the_pentalanine_demo_through_array_native():
    async def probe() -> None:
        source_view = demo["pentalanine"]
        host = InternalRenderWorkerHost(
            RenderWorkerConfig(startup_timeout=30, shutdown_timeout=5)
        )
        view = MolSysView(transport=host.channel)
        try:
            view.load(source_view.molsys, skip_digestion=True)
            diagnostics = await host.launch_worker()
            await host.wait_for_structure(timeout=30)
            manager = view._structure_transfer_manager(None)  # noqa: SLF001

            assert diagnostics.webgl2
            assert not diagnostics.software_rendering
            assert diagnostics.renderer
            expected_renderer = os.environ.get("MSV_EXPECTED_GPU_REGEX")
            if expected_renderer:
                assert re.search(expected_renderer, diagnostics.renderer), (
                    f"renderer {diagnostics.renderer!r} does not match the site "
                    f"certification pattern {expected_renderer!r}"
                )
            assert view._ready is True  # noqa: SLF001
            assert view.molsys.get_n_atoms() == 62
            assert view.molsys.structures.n_structures == 100
            assert manager is not None and not manager.has_active
            assert host.failure is None
            assert host.last_structure_error is None
        finally:
            await host.close()
            view.close()
            source_view.close()

    asyncio.run(probe())
