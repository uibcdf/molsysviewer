"""Shared runtime-envelope contract for the AnyWidget seam (R1).

This module is deliberately top-level and dependency-light (stdlib only) so both
the low-level widget (``molsysviewer/widget.py``) and the viewer
authority (``molsysviewer/viewer/runtime_router.py``) can import it without a
circular import through the ``viewer`` package.

It owns the stateless half of the contract: loading the shared manifest
(``runtime_actions.json``), classifying actions, and wrapping an outbound domain
message into a ``RuntimeEnvelope``. The stateful inbound authority (validation +
command deduplication) lives in ``viewer/runtime_router.py``.
"""

import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

RUNTIME_PROTOCOL_VERSION = 1

# Message ids only need to be unique within a session, and the session id is
# already part of the id. A counter measured ~12x cheaper than uuid4, which
# matters because every outbound projection mints one.
_MESSAGE_SEQUENCE = itertools.count(1)

_MANIFEST_PATH = Path(__file__).resolve().parent / "runtime_actions.json"

_VALID_CATEGORIES = {"command", "event", "request", "ack", "error"}


def _load_manifest() -> tuple[dict[str, str], frozenset[str], frozenset[str], frozenset[str], frozenset[str]]:
    data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    if int(data.get("protocol_version", 0)) != RUNTIME_PROTOCOL_VERSION:
        raise ValueError(
            f"runtime_actions.json protocol_version must be {RUNTIME_PROTOCOL_VERSION}"
        )
    actions = {str(name): str(category) for name, category in data["actions"].items()}
    bad = {name: cat for name, cat in actions.items() if cat not in _VALID_CATEGORIES}
    if bad:
        raise ValueError(f"runtime_actions.json has invalid categories: {bad}")
    outbound_requests = frozenset(str(name) for name in data.get("outbound_requests", ()))
    raw = frozenset(str(name) for name in data.get("raw", ()))
    data_plane = frozenset(str(name) for name in data.get("data_plane", ()))
    qt_transport = frozenset(str(name) for name in data.get("qt_transport", ()))
    groups = [set(actions), set(outbound_requests), set(raw), set(data_plane), set(qt_transport)]
    seen: set[str] = set()
    for group in groups:
        clash = seen & group
        if clash:
            raise ValueError(f"runtime_actions.json action appears in two groups: {clash}")
        seen |= group
    return actions, outbound_requests, raw, data_plane, qt_transport


(
    ACTION_CATEGORIES,
    OUTBOUND_REQUESTS,
    RAW_ACTIONS,
    DATA_PLANE_ACTIONS,
    QT_TRANSPORT_ACTIONS,
) = _load_manifest()


def category_of(action: str) -> str | None:
    """Manifest category for a browser-originated action, or ``None`` if unknown."""
    return ACTION_CATEGORIES.get(action)


def _non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def is_envelope(value: Any) -> bool:
    """True if ``value`` looks like a RuntimeEnvelope rather than a raw message.

    Raw bootstrap/data-plane messages key on ``event``/``op`` and carry none of
    the envelope fields, so this cleanly separates the two shapes and lets
    ``wrap_outbound`` avoid double-wrapping an already-enveloped message.
    """
    if not isinstance(value, Mapping):
        return False
    return (
        isinstance(value.get("protocolVersion"), int)
        and not isinstance(value.get("protocolVersion"), bool)
        and isinstance(value.get("direction"), str)
        and isinstance(value.get("action"), str)
        and "payload" in value
    )


@dataclass(frozen=True)
class RuntimeEnvelope:
    protocol_version: int
    viewer_id: str
    session_id: str
    endpoint_id: str
    message_id: str
    direction: str
    action: str
    payload: Any
    target_endpoint_id: str | None = None
    correlation_id: str | None = None
    generation: int | None = None


def validate_envelope_shape(value: Any) -> RuntimeEnvelope | None:
    """Return a typed envelope, or ``None`` if the raw value is malformed."""
    if not isinstance(value, Mapping):
        return None
    protocol_version = value.get("protocolVersion")
    if not isinstance(protocol_version, int) or isinstance(protocol_version, bool):
        return None
    for key in ("viewerId", "sessionId", "endpointId", "messageId", "direction", "action"):
        if not _non_empty_str(value.get(key)):
            return None
    target = value.get("targetEndpointId")
    if target is not None and not _non_empty_str(target):
        return None
    correlation = value.get("correlationId")
    if correlation is not None and not _non_empty_str(correlation):
        return None
    generation = value.get("generation")
    if generation is not None and (not isinstance(generation, int) or isinstance(generation, bool) or generation < 0):
        return None
    if "payload" not in value:
        return None
    return RuntimeEnvelope(
        protocol_version=protocol_version,
        viewer_id=value["viewerId"],
        session_id=value["sessionId"],
        endpoint_id=value["endpointId"],
        message_id=value["messageId"],
        direction=value["direction"],
        action=value["action"],
        payload=value["payload"],
        target_endpoint_id=target,
        correlation_id=correlation,
        generation=generation,
    )


def action_of(message: Mapping[str, Any]) -> str | None:
    """Python->browser messages key their action on ``op`` (projection ops) or ``event``."""
    for key in ("op", "event"):
        value = message.get(key)
        if _non_empty_str(value):
            return value
    return None


def wrap_outbound(
    message: Mapping[str, Any],
    viewer_id: str,
    session_id: str,
) -> Mapping[str, Any]:
    """Wrap a domain projection/request for delivery over the AnyWidget seam.

    Called by ``MolSysViewerWidget.send`` (the connector owns its wire format).
    ``raw``/``data_plane`` messages and already-enveloped messages (e.g. a
    duplicate-command ack built with its own direction/correlationId) pass
    through unchanged; domain projection ops keep their payload verbatim.
    """
    if is_envelope(message):
        return message
    action = action_of(message)
    if action is None or action in RAW_ACTIONS or action in DATA_PLANE_ACTIONS:
        return message
    direction = "request" if action in OUTBOUND_REQUESTS else "projection"
    return {
        "protocolVersion": RUNTIME_PROTOCOL_VERSION,
        "viewerId": viewer_id,
        "sessionId": session_id,
        "endpointId": f"python:{viewer_id}",
        "targetEndpointId": f"widget-host:{session_id}",
        "messageId": f"py-{session_id}-{next(_MESSAGE_SEQUENCE)}",
        "direction": direction,
        "action": action,
        "payload": message,
    }
