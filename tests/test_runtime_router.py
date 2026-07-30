"""R1 authority side: envelope validation + command deduplication.

Browser-independent, mirroring R0's pure-dispatcher philosophy. Mutation targets
are called out per test: reverting the mechanism under test must turn it red.
"""

from __future__ import annotations

import pytest

from molsysviewer.viewer.runtime_router import (
    ACTION_CATEGORIES,
    DATA_PLANE_ACTIONS,
    OUTBOUND_REQUESTS,
    RAW_ACTIONS,
    RUNTIME_PROTOCOL_VERSION,
    WidgetRuntimeRouter,
)

VIEWER = "view-abc"
SESSION = "session-xyz"


def make_router() -> WidgetRuntimeRouter:
    return WidgetRuntimeRouter(VIEWER, SESSION)


def envelope(action, direction, *, payload=None, message_id="m1", viewer=VIEWER,
             session=SESSION, endpoint=None, target=None):
    return {
        "protocolVersion": RUNTIME_PROTOCOL_VERSION,
        "viewerId": viewer,
        "sessionId": session,
        "endpointId": endpoint if endpoint is not None else f"widget-host:{session}",
        "targetEndpointId": target if target is not None else f"python:{viewer}",
        "messageId": message_id,
        "direction": direction,
        "action": action,
        "payload": payload if payload is not None else {"event": action},
    }


# -- manifest sanity ---------------------------------------------------------

def test_manifest_categories_are_all_valid():
    assert ACTION_CATEGORIES  # non-empty
    assert set(ACTION_CATEGORIES.values()) <= {"command", "event", "request", "ack", "error"}
    # all four groups are pairwise disjoint
    groups = [set(ACTION_CATEGORIES), set(OUTBOUND_REQUESTS), set(RAW_ACTIONS), set(DATA_PLANE_ACTIONS)]
    union = set().union(*groups)
    assert sum(len(g) for g in groups) == len(union)


# -- accepted path + payload identity ---------------------------------------

def test_command_is_accepted_and_payload_is_the_exact_domain_message():
    router = make_router()
    domain = {"event": "interaction_context_action", "op": "add_region", "tag": "A"}
    result = router.route_inbound(envelope("interaction_context_action", "command", payload=domain))
    assert result.status == "accepted"
    # The unwrapped message must be exactly what _handle_frontend_event received before.
    assert result.message is domain


def test_event_is_accepted_without_deduplication():
    router = make_router()
    # Same message_id twice: events are not deduped, so both are accepted.
    first = router.route_inbound(envelope("interaction_hover", "event", message_id="e1"))
    second = router.route_inbound(envelope("interaction_hover", "event", message_id="e1"))
    assert first.status == "accepted"
    assert second.status == "accepted"


# -- deduplication (mutation target: drop _record_command) ------------------

def test_duplicate_command_is_reported_and_not_reapplied():
    router = make_router()
    first = router.route_inbound(envelope("scene_history_undo", "command", message_id="cmd"))
    second = router.route_inbound(envelope("scene_history_undo", "command", message_id="cmd"))
    assert first.status == "accepted"
    assert second.status == "duplicate"
    # An observable ack can be emitted for the duplicate, correlated to the command.
    ack = router.duplicate_ack(second.envelope)
    assert ack["direction"] == "ack"
    assert ack["correlationId"] == "cmd"
    # The ack must satisfy the same action<->payload coherence the browser enforces,
    # or the TS adapter would reject it as action-payload-mismatch.
    assert ack["action"] == "command_duplicate_ack"
    assert ack["payload"]["event"] == ack["action"]


def test_dedup_set_is_bounded_and_evicts_oldest():
    router = WidgetRuntimeRouter(VIEWER, SESSION, max_processed_commands=2)
    for mid in ("a", "b", "c"):  # "a" should be evicted when "c" arrives
        router.route_inbound(envelope("scene_history_undo", "command", message_id=mid))
    # "a" was evicted, so replaying it is treated as new, not duplicate.
    assert router.route_inbound(envelope("scene_history_undo", "command", message_id="a")).status == "accepted"
    # "c" is still remembered.
    assert router.route_inbound(envelope("scene_history_undo", "command", message_id="c")).status == "duplicate"


# -- identity guards (mutation targets: drop each check) --------------------

def test_wrong_viewer_is_rejected():
    router = make_router()
    result = router.route_inbound(envelope("interaction_hover", "event", viewer="view-other"))
    assert result.status == "rejected" and result.reason == "viewer-mismatch"


def test_wrong_session_is_rejected():
    router = make_router()
    result = router.route_inbound(envelope("interaction_hover", "event", session="session-other"))
    assert result.status == "rejected" and result.reason == "session-mismatch"


def test_unexpected_source_endpoint_is_rejected():
    router = make_router()
    result = router.route_inbound(envelope("interaction_hover", "event", endpoint="canvas-popup:999"))
    assert result.status == "rejected" and result.reason == "unknown-source"


def test_unexpected_target_endpoint_is_rejected():
    router = make_router()
    result = router.route_inbound(envelope("interaction_hover", "event", target="python:someone-else"))
    assert result.status == "rejected" and result.reason == "unknown-target"


# -- action / direction contract --------------------------------------------

def test_direction_must_match_manifest_category():
    router = make_router()
    # interaction_context_action is a command; declaring it an event is rejected.
    result = router.route_inbound(envelope("interaction_context_action", "event"))
    assert result.status == "rejected" and result.reason == "direction-mismatch"


def test_unknown_action_is_rejected_not_silently_downgraded():
    router = make_router()
    result = router.route_inbound(envelope("totally_made_up", "event"))
    assert result.status == "rejected" and result.reason == "unknown-action"


def test_envelope_action_must_match_payload_event():
    # A hover envelope must not be able to smuggle a context-action mutation.
    router = make_router()
    smuggle = envelope(
        "interaction_hover", "event",
        payload={"event": "interaction_context_action", "op": "add_region", "tag": "A"},
    )
    result = router.route_inbound(smuggle)
    assert result.status == "rejected" and result.reason == "action-payload-mismatch"


@pytest.mark.parametrize("action", sorted(OUTBOUND_REQUESTS))
def test_outbound_only_requests_are_rejected_from_the_browser(action):
    router = make_router()
    result = router.route_inbound(envelope(action, "request"))
    assert result.status == "rejected" and result.reason == "outbound-only"


@pytest.mark.parametrize("action", sorted(RAW_ACTIONS | DATA_PLANE_ACTIONS))
def test_raw_and_data_plane_actions_must_not_be_enveloped(action):
    router = make_router()
    result = router.route_inbound(envelope(action, "event"))
    assert result.status == "rejected" and result.reason == "not-enveloped"


def test_protocol_mismatch_is_rejected():
    router = make_router()
    env = envelope("interaction_hover", "event")
    env["protocolVersion"] = 999
    assert router.route_inbound(env).reason == "protocol-mismatch"


@pytest.mark.parametrize("missing", ["viewerId", "sessionId", "endpointId", "messageId", "direction", "action"])
def test_malformed_envelope_missing_field_is_rejected(missing):
    router = make_router()
    env = envelope("interaction_hover", "event")
    del env[missing]
    assert router.route_inbound(env).reason == "malformed-envelope"


def test_non_mapping_payload_is_rejected():
    router = make_router()
    env = envelope("interaction_hover", "event")
    env["payload"] = ["not", "a", "mapping"]
    assert router.route_inbound(env).reason == "malformed-payload"


# -- outbound wrapping -------------------------------------------------------

def test_wrap_outbound_projection_keeps_payload_and_stamps_identity():
    router = make_router()
    op = {"op": "set_region_summaries", "summaries": []}
    env = router.wrap_outbound(op)
    assert env["direction"] == "projection"
    assert env["endpointId"] == f"python:{VIEWER}"
    assert env["targetEndpointId"] == f"widget-host:{SESSION}"
    assert env["action"] == "set_region_summaries"
    assert env["payload"] is op


def test_wrap_outbound_uses_request_direction_for_outbound_requests():
    router = make_router()
    assert "request_camera_snapshot" in OUTBOUND_REQUESTS
    env = router.wrap_outbound({"op": "request_camera_snapshot"})
    assert env["direction"] == "request"


@pytest.mark.parametrize("action", sorted(RAW_ACTIONS | DATA_PLANE_ACTIONS))
def test_wrap_outbound_leaves_raw_and_data_plane_untouched(action):
    router = make_router()
    msg = {"event": action}
    assert router.wrap_outbound(msg) is msg
