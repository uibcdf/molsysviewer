"""RRS0 remote-session identity, placement and authority contract."""

from __future__ import annotations

import pytest
from molsysviewer.remote import SessionRuntimeRouter
from molsysviewer.runtime_contract import (
    ENDPOINT_CAPABILITIES,
    ENDPOINT_ROLE_CAPABILITIES,
    RENDER_PLACEMENTS,
    RUNTIME_PROTOCOL_VERSION,
    validate_envelope_shape,
)

VIEWER = "view-remote"
SESSION = "session-remote"


def client_capabilities(render_on: str, *, qt: bool = False) -> set[str]:
    value = {"command-origin", "input-send", "workbench"}
    if qt:
        value.add("native-host")
    if render_on == "client":
        value.update({"render", "structure-receive"})
    else:
        value.add("video-receive")
    return value


def register_client(router: SessionRuntimeRouter, *, qt: bool = False) -> str:
    endpoint_id = "qt-client:one" if qt else "browser-client:one"
    router.register_endpoint(
        endpoint_id,
        "qt-client" if qt else "browser-client",
        client_capabilities(router.render_on, qt=qt),
        actor_id="human:one",
        actor_kind="human",
    )
    return endpoint_id


def register_worker(router: SessionRuntimeRouter) -> str:
    endpoint_id = "render-worker:one"
    router.register_endpoint(
        endpoint_id,
        "render-worker",
        {"input-receive", "render", "structure-receive", "video-send"},
        actor_id="system:worker-one",
        actor_kind="system",
    )
    return endpoint_id


def envelope(
    endpoint_id: str,
    action: str = "scene_history_undo",
    direction: str = "command",
    *,
    message_id: str = "command-1",
    actor_id: str | None = "human:one",
    actor_kind: str | None = "human",
    viewer_id: str = VIEWER,
    session_id: str = SESSION,
) -> dict:
    value = {
        "protocolVersion": RUNTIME_PROTOCOL_VERSION,
        "viewerId": viewer_id,
        "sessionId": session_id,
        "endpointId": endpoint_id,
        "targetEndpointId": f"python:{VIEWER}",
        "messageId": message_id,
        "direction": direction,
        "action": action,
        "payload": {"event": action},
    }
    if actor_id is not None:
        value["actorId"] = actor_id
    if actor_kind is not None:
        value["actorKind"] = actor_kind
    return value


def test_shared_remote_vocabulary_is_complete_and_role_bounded():
    assert RENDER_PLACEMENTS == {"client", "server"}
    assert {"browser-client", "qt-client", "render-worker", "agent"} <= set(
        ENDPOINT_ROLE_CAPABILITIES
    )
    assert ENDPOINT_CAPABILITIES == frozenset().union(
        *ENDPOINT_ROLE_CAPABILITIES.values()
    )
    assert "authority" in ENDPOINT_ROLE_CAPABILITIES["python"]
    assert "native-host" in ENDPOINT_ROLE_CAPABILITIES["qt-client"]
    assert "video-send" in ENDPOINT_ROLE_CAPABILITIES["render-worker"]


@pytest.mark.parametrize("render_on", ["client", "server"])
@pytest.mark.parametrize("qt", [False, True])
def test_browser_and_qt_clients_register_in_both_explicit_placements(render_on, qt):
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on=render_on)
    endpoint_id = register_client(router, qt=qt)
    registration = router.endpoint(endpoint_id)

    assert registration is not None
    assert registration.actor_kind == "human"
    assert ("render" in registration.capabilities) is (render_on == "client")
    assert ("structure-receive" in registration.capabilities) is (render_on == "client")
    assert ("video-receive" in registration.capabilities) is (render_on == "server")


def test_server_rendering_registers_one_worker_and_routes_rendering_only_to_it():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    client = register_client(router, qt=True)
    worker = register_worker(router)

    assert router.rendering_endpoint_ids() == (worker,)
    assert router.projection_endpoint_ids() == (client, worker)
    with pytest.raises(ValueError, match="already registered"):
        register_worker(router)


def test_client_rendering_rejects_worker_and_server_rendering_rejects_hidden_local_render():
    local = SessionRuntimeRouter(VIEWER, SESSION, render_on="client")
    with pytest.raises(ValueError, match="invalid when render_on='client'"):
        register_worker(local)

    remote = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    with pytest.raises(ValueError, match="may not activate capabilities"):
        remote.register_endpoint(
            "browser-client:bad",
            "browser-client",
            client_capabilities("server") | {"render", "structure-receive"},
            actor_id="human:one",
            actor_kind="human",
        )


def test_role_cannot_claim_a_capability_outside_the_shared_manifest():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    with pytest.raises(ValueError, match="may not claim"):
        router.register_endpoint(
            "render-worker:bad",
            "render-worker",
            {"input-receive", "render", "structure-receive", "video-send", "native-host"},
            actor_id="system:worker",
            actor_kind="system",
        )


def test_one_remote_human_client_is_the_pre_1_0_limit():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    register_client(router)
    with pytest.raises(ValueError, match="already registered"):
        router.register_endpoint(
            "qt-client:two",
            "qt-client",
            client_capabilities("server", qt=True),
            actor_id="human:two",
            actor_kind="human",
        )


def test_authenticated_command_is_accepted_once_and_duplicate_is_not_reapplied():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    endpoint_id = register_client(router)
    command = envelope(endpoint_id)

    first = router.route_inbound(command)
    second = router.route_inbound(command)

    assert first.status == "accepted"
    assert first.recipient_endpoint_ids == (router.python_endpoint,)
    assert second.status == "duplicate"
    assert second.recipient_endpoint_ids == ()


def test_stale_session_wrong_actor_and_unknown_endpoint_are_rejected_before_dispatch():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    endpoint_id = register_client(router)

    stale = router.route_inbound(envelope(endpoint_id, session_id="session-old"))
    actor = router.route_inbound(envelope(endpoint_id, actor_id="human:other"))
    unknown = router.route_inbound(envelope("browser-client:unknown"))

    assert stale.reason == "session-mismatch"
    assert actor.reason == "actor-mismatch"
    assert unknown.reason == "unknown-source"


def test_non_command_endpoint_cannot_smuggle_a_command():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    router.register_endpoint("canvas:one", "canvas", {"render", "structure-receive"})
    result = router.route_inbound(
        envelope("canvas:one", actor_id=None, actor_kind=None)
    )
    assert result.status == "rejected"
    assert result.reason == "capability-mismatch"


def test_agent_identity_is_reserved_on_the_same_command_gateway():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    router.register_endpoint(
        "agent:one",
        "agent",
        {"command-origin"},
        actor_id="molsys-ai:one",
        actor_kind="agent",
    )
    result = router.route_inbound(
        envelope(
            "agent:one",
            actor_id="molsys-ai:one",
            actor_kind="agent",
        )
    )
    assert result.status == "accepted"
    assert result.recipient_endpoint_ids == (router.python_endpoint,)


def test_python_projection_preserves_actor_causation_operation_and_deadline_metadata():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    endpoint_id = register_client(router)
    projected = {"op": "set_region_summaries", "summaries": []}

    value = router.wrap_outbound(
        projected,
        target_endpoint_id=endpoint_id,
        correlation_id="command-1",
        causation_id="request-1",
        operation_id="operation-1",
        deadline_unix_ms=2_000_000_000_000,
    )
    typed = validate_envelope_shape(value)

    assert typed is not None
    assert typed.payload is projected
    assert typed.actor_kind == "system"
    assert typed.correlation_id == "command-1"
    assert typed.causation_id == "request-1"
    assert typed.operation_id == "operation-1"
    assert typed.deadline_unix_ms == 2_000_000_000_000


@pytest.mark.parametrize(
    "update",
    [
        {"actorId": "human:one"},
        {"actorId": "human:one", "actorKind": "robot"},
        {"causationId": ""},
        {"operationId": ""},
        {"deadlineUnixMs": -1},
        {"deadlineUnixMs": True},
    ],
)
def test_malformed_provenance_metadata_is_rejected(update):
    value = envelope("browser-client:one")
    value.update(update)
    if "actorId" in update and "actorKind" not in update:
        value.pop("actorKind", None)
    assert validate_envelope_shape(value) is None


def test_endpoint_close_revokes_identity_without_touching_python_authority():
    router = SessionRuntimeRouter(VIEWER, SESSION, render_on="server")
    endpoint_id = register_client(router)
    assert router.unregister_endpoint(endpoint_id) is True
    assert router.route_inbound(envelope(endpoint_id)).reason == "unknown-source"
    with pytest.raises(ValueError, match="cannot be unregistered"):
        router.unregister_endpoint(router.python_endpoint)
