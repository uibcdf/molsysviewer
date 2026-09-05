"""RRS2 authenticated browser-session gateway tests over real loopback sockets."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import aiohttp
import pytest
from molsysviewer.remote import RemoteSessionService
from molsysviewer.viewer import MolSysView
from yarl import URL

PDB_TEXT = b"""\
ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""


def test_worker_monitor_recovers_once_and_renegotiates_the_attached_client():
    class FakeSocket:
        def __init__(self):
            self.closed = False
            self.messages = []

        async def send_json(self, value):
            self.messages.append(value)

        async def close(self, **_kwargs):
            self.closed = True

    class FakeWorker:
        def __init__(self):
            self.state = "failed"
            self.failure = "Chromium exited unexpectedly with code 9"
            self.config = SimpleNamespace(shutdown_timeout=1.0, startup_timeout=1.0)

        async def refresh_state(self):
            return self.state

        async def close(self):
            self.state = "stopped"

    async def probe() -> None:
        service = RemoteSessionService(ice_servers=({"urls": "stun:example.test"},))
        view = MolSysView(transport=service.channel)
        socket = FakeSocket()
        worker = FakeWorker()
        host = service.worker_host
        host.worker = worker
        host.worker_connected.set()
        service._client_socket = socket  # noqa: SLF001
        service._client_registered = True  # noqa: SLF001

        async def restart_worker():
            worker.state = "ready"
            host.worker_connected.set()
            return SimpleNamespace(pid=2)

        host.restart_worker = restart_worker
        service._worker_monitor_task = asyncio.create_task(  # noqa: SLF001
            service._monitor_worker()  # noqa: SLF001
        )
        try:
            await asyncio.wait_for(
                _wait_until(lambda: service.worker_recovery_count == 1), timeout=2
            )
            assert service.worker_recovery_state == "recovered"
            assert service.failure is None
            assert socket.messages == [
                {
                    "kind": "session-state",
                    "state": "recovering",
                    "detail": "Chromium exited unexpectedly with code 9",
                },
                {"kind": "session-state", "state": "recovered"},
            ]
            kind, peer_start = host._queue.get_nowait()  # noqa: SLF001
            assert kind == "wire"
            assert peer_start == {
                "kind": "peer-start",
                "clientEndpointId": service.client_endpoint_id,
                "actorId": service.client_actor_id,
                "iceServers": [{"urls": "stun:example.test"}],
            }
            await asyncio.sleep(0.55)
            assert service.worker_recovery_count == 1
        finally:
            await service.close()
            view.close()

    async def _wait_until(predicate):
        while not predicate():
            await asyncio.sleep(0.01)

    asyncio.run(probe())


def _registration(service: RemoteSessionService) -> dict:
    capabilities = ["command-origin", "input-send", "workbench"]
    if service.render_on == "server":
        capabilities.append("video-receive")
    else:
        capabilities.extend(["render", "structure-receive"])
    return {
        "kind": "register",
        "protocolVersion": 1,
        "viewerId": service.channel.router.viewer_id,
        "sessionId": service.channel.router.session_id,
        "endpointId": service.client_endpoint_id,
        "role": "browser-client",
        "actorId": service.client_actor_id,
        "actorKind": "human",
        "capabilities": capabilities,
    }


def test_client_rendering_uses_the_same_authenticated_gateway_without_a_worker():
    async def probe() -> None:
        service = RemoteSessionService(render_on="client")
        view = MolSysView(transport=service.channel)
        try:
            client_url = await service.start()
            split = urlsplit(client_url)
            token = parse_qs(split.fragment)["token"][0]
            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": token},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 200
                async with session.get(f"{service.origin}/session/config") as response:
                    config = await response.json()
                    assert config["renderOn"] == "client"
                    assert config["workerEndpointId"] is None
                async with session.ws_connect(
                    f"{service.origin}/session/ws",
                    origin=service.origin,
                    protocols=("molsysviewer-session-v1",),
                ) as socket:
                    await socket.send_json(_registration(service))
                    assert await socket.receive_json(timeout=2) == {"kind": "registered"}
                    await socket.send_json(
                        {
                            "kind": "raw",
                            "message": {
                                "event": "ready",
                                "capabilities": {"binary_structure_data": [1]},
                            },
                        }
                    )
                    for _ in range(100):
                        if view._ready:  # noqa: SLF001
                            break
                        await asyncio.sleep(0.01)
                    assert view._ready is True  # noqa: SLF001

                    service.channel.send({"op": "set_panel_mode", "mode": "studio"})
                    for _ in range(30):
                        wire = await socket.receive_json(timeout=2)
                        if wire.get("kind") == "control" and wire["envelope"].get(
                            "action"
                        ) == "set_panel_mode":
                            break
                    else:
                        raise AssertionError("client renderer received no control projection")
                    assert wire["envelope"]["payload"] == {
                        "op": "set_panel_mode",
                        "mode": "studio",
                    }
        finally:
            await service.close()
            view.close()

    asyncio.run(probe())


def _signal(service: RemoteSessionService, endpoint_id: str, kind: str) -> dict:
    payload = {"sdp": "v=0\r\n"} if kind in {"offer", "answer"} else {}
    return {
        "protocolVersion": 1,
        "viewerId": service.channel.router.viewer_id,
        "sessionId": service.channel.router.session_id,
        "endpointId": endpoint_id,
        "messageId": f"{endpoint_id}:signal:1",
        "kind": kind,
        "payload": payload,
    }


def _input(service: RemoteSessionService) -> dict:
    return {
        "protocolVersion": 1,
        "viewerId": service.channel.router.viewer_id,
        "sessionId": service.channel.router.session_id,
        "endpointId": service.client_endpoint_id,
        "sequence": 1,
        "timestampMs": 1.0,
        "kind": "pointer",
        "viewport": {"width": 800, "height": 600, "devicePixelRatio": 1},
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


def _panel_snapshot_request(service: RemoteSessionService) -> dict:
    return {
        "protocolVersion": 1,
        "viewerId": service.channel.router.viewer_id,
        "sessionId": service.channel.router.session_id,
        "endpointId": service.client_endpoint_id,
        "targetEndpointId": service.channel.router.python_endpoint,
        "messageId": "browser-panel-snapshot-1",
        "operationId": "browser-panel-snapshot-1",
        "direction": "request",
        "action": "request_popup_scene_snapshot",
        "payload": {
            "event": "request_popup_scene_snapshot",
            "mode": "panel",
            "popup_endpoint_id": service.client_endpoint_id,
        },
        "actorId": service.client_actor_id,
        "actorKind": "human",
    }


def test_session_auth_registration_signaling_input_and_command_share_one_identity():
    async def probe() -> None:
        service = RemoteSessionService()
        view = MolSysView(transport=service.channel)
        try:
            client_url = await service.start()
            split = urlsplit(client_url)
            token = parse_qs(split.fragment)["token"][0]
            clean_client_url = f"{split.scheme}://{split.netloc}{split.path}"
            assert split.query == ""
            assert token not in clean_client_url

            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                async with session.get(clean_client_url) as response:
                    html = await response.text()
                    assert response.status == 200
                    assert token not in html
                async with session.get(f"{service.origin}/session/config") as response:
                    assert response.status == 403
                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": "wrong"},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 403
                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": token},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 200
                    cookie = response.cookies[service._cookie_name]  # noqa: SLF001
                    assert cookie["httponly"] is True
                async with session.get(f"{service.origin}/session/config") as response:
                    config = await response.json()
                    assert config["endpointId"] == service.client_endpoint_id
                    assert config["workerEndpointId"] == service.worker_host.endpoint_id

                artifact_url = service._publish_download(  # noqa: SLF001
                    "figure.png", "image/png", b"\x89PNG\r\n\x1a\n"
                )
                async with aiohttp.ClientSession() as unauthenticated:
                    async with unauthenticated.get(
                        f"{service.origin}{artifact_url}"
                    ) as response:
                        assert response.status == 403
                async with session.get(f"{service.origin}{artifact_url}") as response:
                    assert response.status == 200
                    assert await response.read() == b"\x89PNG\r\n\x1a\n"
                    assert response.headers["Content-Disposition"] == (
                        'attachment; filename="figure.png"'
                    )

                upload = aiohttp.FormData()
                upload.add_field(
                    "file",
                    PDB_TEXT,
                    filename="uploaded.pdb",
                    content_type="chemical/x-pdb",
                )
                async with session.post(
                    f"{service.origin}/session/upload",
                    data=upload,
                    headers={"Origin": service.origin},
                ) as response:
                    uploaded = await response.json()
                    assert response.status == 200
                    assert uploaded == {
                        "uploaded": True,
                        "filename": "uploaded.pdb",
                        "n_atoms": 4,
                        "n_structures": 1,
                    }
                    assert view._last_label == "uploaded"  # noqa: SLF001

                unsupported = aiohttp.FormData()
                unsupported.add_field("file", b"not molecular", filename="notes.txt")
                async with session.post(
                    f"{service.origin}/session/upload",
                    data=unsupported,
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 415

                async with session.ws_connect(
                    f"{service.origin}/session/ws",
                    origin=service.origin,
                    protocols=("molsysviewer-session-v1",),
                ) as socket:
                    await socket.send_json(_registration(service))
                    assert await socket.receive_json(timeout=2) == {"kind": "registered"}
                    await asyncio.wait_for(service.client_registered.wait(), timeout=2)
                    endpoint = service.channel.router.endpoint(service.client_endpoint_id)
                    assert endpoint is not None and endpoint.actor_kind == "human"

                    kind, peer_start = await asyncio.wait_for(
                        service.worker_host._queue.get(), timeout=2  # noqa: SLF001
                    )
                    assert kind == "wire"
                    assert peer_start["kind"] == "peer-start"
                    assert peer_start["clientEndpointId"] == service.client_endpoint_id

                    await socket.send_json(
                        {"kind": "control", "envelope": _panel_snapshot_request(service)}
                    )
                    # Client and server intentionally share this test's event
                    # loop; let the loopback client writer flush before awaiting
                    # the correlated reply on that same loop. Production peers
                    # run in separate processes.
                    await asyncio.sleep(0.05)
                    snapshot_wire = await socket.receive_json(timeout=2)
                    assert snapshot_wire["kind"] == "control"
                    snapshot = snapshot_wire["envelope"]
                    assert snapshot["action"] == "popup_scene_snapshot"
                    assert snapshot["targetEndpointId"] == service.client_endpoint_id
                    assert snapshot["correlationId"] == "browser-panel-snapshot-1"
                    ops = {item.get("op") for item in snapshot["payload"]["messages"]}
                    assert "set_whole_summary" in ops
                    assert "set_region_summaries" in ops
                    assert "load_molsys_payload" not in ops

                    answer = _signal(service, service.client_endpoint_id, "answer")
                    await socket.send_json({"kind": "signal", "packet": answer})
                    kind, worker_signal = await asyncio.wait_for(
                        service.worker_host._queue.get(), timeout=2  # noqa: SLF001
                    )
                    assert kind == "wire"
                    assert worker_signal == {"kind": "signal", "packet": answer}

                    offer = _signal(service, service.worker_host.endpoint_id, "offer")
                    await service._forward_worker_signal(offer)  # noqa: SLF001
                    assert await socket.receive_json(timeout=2) == {
                        "kind": "signal",
                        "packet": offer,
                    }

                    input_packet = _input(service)
                    await socket.send_json({"kind": "input", "packet": input_packet})
                    kind, worker_input = await asyncio.wait_for(
                        service.worker_host._queue.get(), timeout=2  # noqa: SLF001
                    )
                    assert kind == "input"
                    assert worker_input == {"kind": "input", "packet": input_packet}

                    command = {
                        "protocolVersion": 1,
                        "viewerId": service.channel.router.viewer_id,
                        "sessionId": service.channel.router.session_id,
                        "endpointId": service.client_endpoint_id,
                        "targetEndpointId": service.channel.router.python_endpoint,
                        "messageId": "browser-command-1",
                        "direction": "command",
                        "action": "interaction_active_selection_changed",
                        "payload": {
                            "event": "interaction_active_selection_changed",
                            "atom_indices": [1, 2],
                        },
                        "actorId": service.client_actor_id,
                        "actorKind": "human",
                    }
                    await socket.send_json({"kind": "control", "envelope": command})
                    for _ in range(100):
                        if sorted(view.active_selection.atom_indices) == [1, 2]:
                            break
                        await asyncio.sleep(0.01)
                    assert sorted(view.active_selection.atom_indices) == [1, 2]

                    close_task = asyncio.create_task(service.close())
                    assert await socket.receive_json(timeout=2) == {
                        "kind": "session-closing"
                    }
                    await asyncio.wait_for(close_task, timeout=2)
            for _ in range(20):
                if service.channel.router.endpoint(service.client_endpoint_id) is None:
                    break
                await asyncio.sleep(0.01)
            assert service.channel.router.endpoint(service.client_endpoint_id) is None
        finally:
            await service.close()
            view.close()

    asyncio.run(probe())


def test_two_loopback_sessions_keep_cookies_and_artifacts_isolated():
    async def probe() -> None:
        first = RemoteSessionService(render_on="client")
        second = RemoteSessionService(render_on="client")
        first_view = MolSysView(transport=first.channel)
        second_view = MolSysView(transport=second.channel)
        try:
            first_url, second_url = await asyncio.gather(first.start(), second.start())
            first_token = parse_qs(urlsplit(first_url).fragment)["token"][0]
            second_token = parse_qs(urlsplit(second_url).fragment)["token"][0]
            assert first._cookie_name != second._cookie_name  # noqa: SLF001
            assert first.channel.router.session_id != second.channel.router.session_id

            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                for service, token in ((first, first_token), (second, second_token)):
                    async with session.post(
                        f"{service.origin}/session/auth",
                        json={"token": token},
                        headers={"Origin": service.origin},
                    ) as response:
                        assert response.status == 200

                # Cookies are scoped by host/path rather than port. Unique names
                # let one browser remain authenticated to both loopback sessions.
                cookies = jar.filter_cookies(URL(f"{first.origin}/session/config"))
                assert first._cookie_name in cookies  # noqa: SLF001
                assert second._cookie_name in cookies  # noqa: SLF001

                async with session.get(f"{first.origin}/session/config") as response:
                    assert response.status == 200
                    assert (await response.json())["sessionId"] == first.channel.router.session_id
                async with session.get(f"{second.origin}/session/config") as response:
                    assert response.status == 200
                    assert (await response.json())["sessionId"] == second.channel.router.session_id

                first_artifact = first._publish_download(  # noqa: SLF001
                    "first.txt", "text/plain", b"first-session"
                )
                async with session.get(f"{second.origin}{first_artifact}") as response:
                    assert response.status == 404
                async with session.get(f"{first.origin}{first_artifact}") as response:
                    assert response.status == 200
                    assert await response.read() == b"first-session"

                async with session.post(
                    f"{second.origin}/session/auth",
                    json={"token": first_token},
                    headers={"Origin": second.origin},
                ) as response:
                    assert response.status == 403
        finally:
            await asyncio.gather(first.close(), second.close())
            first_view.close()
            second_view.close()

    asyncio.run(probe())


def test_rejected_websocket_peers_do_not_poison_health_or_consume_the_client_slot():
    async def probe() -> None:
        service = RemoteSessionService(render_on="client")
        view = MolSysView(transport=service.channel)
        try:
            client_url = await service.start()
            token = parse_qs(urlsplit(client_url).fragment)["token"][0]
            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": token},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 200

                with pytest.raises(aiohttp.WSServerHandshakeError) as wrong_origin:
                    await session.ws_connect(
                        f"{service.origin}/session/ws",
                        origin="http://attacker.invalid",
                        protocols=("molsysviewer-session-v1",),
                    )
                assert wrong_origin.value.status == 403

                with pytest.raises(aiohttp.WSServerHandshakeError) as wrong_protocol:
                    await session.ws_connect(
                        f"{service.origin}/session/ws",
                        origin=service.origin,
                        protocols=("wrong-protocol",),
                    )
                assert wrong_protocol.value.status == 403

                async with session.ws_connect(
                    f"{service.origin}/session/ws",
                    origin=service.origin,
                    protocols=("molsysviewer-session-v1",),
                ) as malformed:
                    await malformed.send_json({"kind": "register", "sessionId": "wrong"})
                    message = await malformed.receive(timeout=2)
                    assert message.type is aiohttp.WSMsgType.CLOSE
                    assert message.data == 1008

                for _ in range(100):
                    if service._client_socket is None:  # noqa: SLF001
                        break
                    await asyncio.sleep(0.01)
                assert service._client_socket is None  # noqa: SLF001
                assert service.failure is None
                assert service.last_client_error == "client registration capabilities are malformed"

                async with session.ws_connect(
                    f"{service.origin}/session/ws",
                    origin=service.origin,
                    protocols=("molsysviewer-session-v1",),
                ) as valid:
                    await valid.send_json(_registration(service))
                    assert await valid.receive_json(timeout=2) == {"kind": "registered"}
                    assert service.channel.router.endpoint(service.client_endpoint_id) is not None
                assert service.failure is None
        finally:
            await service.close()
            view.close()

    asyncio.run(probe())


def test_authentication_failures_are_bounded_without_locking_out_the_valid_token():
    async def probe() -> None:
        service = RemoteSessionService(render_on="client")
        view = MolSysView(transport=service.channel)
        try:
            client_url = await service.start()
            token = parse_qs(urlsplit(client_url).fragment)["token"][0]
            async with aiohttp.ClientSession() as session:
                for attempt in range(8):
                    async with session.post(
                        f"{service.origin}/session/auth",
                        json={"token": f"wrong-{attempt}"},
                        headers={"Origin": service.origin},
                    ) as response:
                        assert response.status == 403
                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": "wrong-again"},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 429
                    assert response.headers["Retry-After"] == "60"

                # The limiter suppresses guessing, not possession of the actual
                # bearer credential. A legitimate client can still recover.
                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": token},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 200
                assert not service._auth_failures  # noqa: SLF001
        finally:
            await service.close()
            view.close()

    asyncio.run(probe())


def test_auth_and_client_websocket_have_limits_separate_from_molecular_uploads():
    async def probe() -> None:
        service = RemoteSessionService(render_on="client")
        view = MolSysView(transport=service.channel)
        try:
            client_url = await service.start()
            token = parse_qs(urlsplit(client_url).fragment)["token"][0]
            jar = aiohttp.CookieJar(unsafe=True)
            async with aiohttp.ClientSession(cookie_jar=jar) as session:
                async with session.post(
                    f"{service.origin}/session/auth",
                    data=b"x" * 4097,
                    headers={
                        "Content-Type": "application/json",
                        "Origin": service.origin,
                    },
                ) as response:
                    assert response.status == 413

                async with session.post(
                    f"{service.origin}/session/auth",
                    json={"token": token},
                    headers={"Origin": service.origin},
                ) as response:
                    assert response.status == 200

                async with session.ws_connect(
                    f"{service.origin}/session/ws",
                    origin=service.origin,
                    protocols=("molsysviewer-session-v1",),
                ) as socket:
                    await socket.send_json(_registration(service))
                    assert await socket.receive_json(timeout=2) == {"kind": "registered"}
                    await socket.send_str("x" * (1024 * 1024 + 1))
                    message = await socket.receive(timeout=2)
                    assert message.type in {
                        aiohttp.WSMsgType.CLOSE,
                        aiohttp.WSMsgType.CLOSED,
                        aiohttp.WSMsgType.ERROR,
                    }

            for _ in range(20):
                if service.channel.router.endpoint(service.client_endpoint_id) is None:
                    break
                await asyncio.sleep(0.01)
            assert service.channel.router.endpoint(service.client_endpoint_id) is None
        finally:
            await service.close()
            view.close()

    asyncio.run(probe())
