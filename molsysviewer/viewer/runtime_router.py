"""Inbound envelope authority + command deduplication for the AnyWidget seam.

Python is the single authority for the ``widget-host`` <-> ``python`` connector.
The browser widget host is one logical endpoint; it does not run its own router
(unlike the popup topology, which fans out across several browser endpoints).

The stateless half of the contract (manifest loading, classification, outbound
wrapping) lives in :mod:`molsysviewer.runtime_contract` and is re-exported here.
This module owns the stateful half: validating inbound envelopes and
deduplicating commands so one accepted command yields one public-API mutation
and one history checkpoint. The unwrapped payload handed back is exactly the
``content`` dict that ``_handle_frontend_event`` received before envelopes.
"""

from dataclasses import dataclass
from typing import Any, Mapping

from ..runtime_contract import (
    ACTION_CATEGORIES,
    DATA_PLANE_ACTIONS,
    OUTBOUND_REQUESTS,
    RAW_ACTIONS,
    RUNTIME_PROTOCOL_VERSION,
    RuntimeEnvelope,
    _non_empty_str,
    category_of,
    is_envelope,
    validate_envelope_shape,
    wrap_outbound,
)

__all__ = [
    "ACTION_CATEGORIES",
    "DATA_PLANE_ACTIONS",
    "OUTBOUND_REQUESTS",
    "RAW_ACTIONS",
    "RUNTIME_PROTOCOL_VERSION",
    "RuntimeEnvelope",
    "RouteResult",
    "WidgetRuntimeRouter",
    "category_of",
    "is_envelope",
    "validate_envelope_shape",
    "wrap_outbound",
]


@dataclass(frozen=True)
class RouteResult:
    status: str  # "accepted" | "duplicate" | "rejected"
    message: Mapping[str, Any] | None = None
    envelope: RuntimeEnvelope | None = None
    reason: str | None = None
    detail: str | None = None


class WidgetRuntimeRouter:
    """Validate inbound envelopes and dedupe commands for the AnyWidget seam.

    A single instance belongs to one ``MolSysView`` (``viewer_id``) and one live
    attachment (``session_id``). Only the matching ``widget-host`` endpoint may
    originate messages; only ``command`` messages are deduplicated, through a
    bounded per-session set of processed ``messageId`` values.
    """

    def __init__(self, viewer_id: str, session_id: str, max_processed_commands: int = 1024) -> None:
        if not _non_empty_str(viewer_id):
            raise ValueError("viewer_id must be a non-empty string")
        if not _non_empty_str(session_id):
            raise ValueError("session_id must be a non-empty string")
        if not isinstance(max_processed_commands, int) or max_processed_commands < 1:
            raise ValueError("max_processed_commands must be a positive integer")
        self.viewer_id = viewer_id
        self.session_id = session_id
        self._max_processed_commands = max_processed_commands
        self.python_endpoint = f"python:{viewer_id}"
        self.widget_host_endpoint = f"widget-host:{session_id}"
        self._processed_commands: dict[str, None] = {}
        # A per-session counter, like the TypeScript side. Ids only need to be
        # unique within the session, and uuid4 measured ~12x more expensive.
        self._message_counter = 0

    def _next_message_id(self) -> str:
        self._message_counter += 1
        return f"py-{self.session_id}-{self._message_counter}"

    # -- inbound (widget-host -> python) -------------------------------------

    def route_inbound(self, value: Any) -> RouteResult:
        envelope = validate_envelope_shape(value)
        if envelope is None:
            return RouteResult("rejected", reason="malformed-envelope", detail="Runtime envelope is malformed")
        if envelope.protocol_version != RUNTIME_PROTOCOL_VERSION:
            return RouteResult("rejected", reason="protocol-mismatch", detail=f"Unsupported protocol {envelope.protocol_version}")
        if envelope.viewer_id != self.viewer_id:
            return RouteResult("rejected", reason="viewer-mismatch", detail=f"Envelope belongs to viewer {envelope.viewer_id}")
        if envelope.session_id != self.session_id:
            return RouteResult("rejected", reason="session-mismatch", detail=f"Envelope belongs to session {envelope.session_id}")
        if envelope.endpoint_id != self.widget_host_endpoint:
            return RouteResult("rejected", reason="unknown-source", detail=f"Unexpected source endpoint {envelope.endpoint_id}")
        if envelope.target_endpoint_id is not None and envelope.target_endpoint_id != self.python_endpoint:
            return RouteResult("rejected", reason="unknown-target", detail=f"Unexpected target endpoint {envelope.target_endpoint_id}")

        action = envelope.action
        if action in RAW_ACTIONS or action in DATA_PLANE_ACTIONS:
            return RouteResult("rejected", reason="not-enveloped", detail=f"Action {action} must not be enveloped")
        if action in OUTBOUND_REQUESTS:
            return RouteResult("rejected", reason="outbound-only", detail=f"Action {action} is Python-originated only")
        category = category_of(action)
        if category is None:
            return RouteResult("rejected", reason="unknown-action", detail=f"Unknown runtime action {action}")
        if envelope.direction != category:
            return RouteResult(
                "rejected",
                reason="direction-mismatch",
                detail=f"Action {action} is {category} but envelope declares {envelope.direction}",
            )

        if not isinstance(envelope.payload, Mapping):
            return RouteResult("rejected", reason="malformed-payload", detail=f"Action {action} payload is not a mapping")
        # Coherence guard: the envelope action must equal the payload's own action
        # key, or a hover envelope could smuggle a context-action mutation past
        # classification and deduplication. Browser->Python payloads key on `event`.
        if envelope.payload.get("event") != action:
            return RouteResult(
                "rejected",
                reason="action-payload-mismatch",
                detail=f"Envelope action {action} does not match payload event {envelope.payload.get('event')!r}",
            )

        if category == "command":
            if envelope.message_id in self._processed_commands:
                return RouteResult("duplicate", message=envelope.payload, envelope=envelope)
            self._record_command(envelope.message_id)

        return RouteResult("accepted", message=envelope.payload, envelope=envelope)

    def _record_command(self, message_id: str) -> None:
        self._processed_commands[message_id] = None
        while len(self._processed_commands) > self._max_processed_commands:
            oldest = next(iter(self._processed_commands))
            del self._processed_commands[oldest]

    # -- outbound (python -> widget-host) ------------------------------------

    def wrap_outbound(self, message: Mapping[str, Any]) -> Mapping[str, Any]:
        """Convenience wrapper delegating to the shared contract function."""
        return wrap_outbound(message, self.viewer_id, self.session_id)

    def correlated_projection(
        self,
        request: RuntimeEnvelope,
        action: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Answer a browser ``request`` with a correlated projection.

        Targeted at the widget host, which routes it onward to the endpoint that
        asked. ``payload['event']`` must equal ``action`` so the browser's
        action<->payload coherence guard accepts it.
        """
        return {
            "protocolVersion": RUNTIME_PROTOCOL_VERSION,
            "viewerId": self.viewer_id,
            "sessionId": self.session_id,
            "endpointId": self.python_endpoint,
            "targetEndpointId": self.widget_host_endpoint,
            "messageId": self._next_message_id(),
            "correlationId": request.message_id,
            "direction": "projection",
            "action": action,
            "payload": dict(payload),
        }

    def duplicate_ack(self, envelope: RuntimeEnvelope) -> dict[str, Any]:
        """An observable ack for a deduplicated command, without re-applying it.

        The envelope action equals its payload action key so the browser's
        action<->payload coherence guard accepts it; the original command is
        referenced through ``correlationId``, not the action. It is already an
        envelope, so ``wrap_outbound`` passes it through unchanged.
        """
        return {
            "protocolVersion": RUNTIME_PROTOCOL_VERSION,
            "viewerId": self.viewer_id,
            "sessionId": self.session_id,
            "endpointId": self.python_endpoint,
            "targetEndpointId": self.widget_host_endpoint,
            "messageId": self._next_message_id(),
            "correlationId": envelope.message_id,
            "direction": "ack",
            "action": "command_duplicate_ack",
            "payload": {"event": "command_duplicate_ack", "message_id": envelope.message_id},
        }
