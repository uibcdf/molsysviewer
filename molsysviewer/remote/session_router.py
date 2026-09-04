"""Pure authority-side routing contract for a remote MolSysViewer session.

This module opens no sockets and launches no worker. It owns the RRS0 identity,
render-placement, endpoint-capability and command-deduplication rules that a
later HTTP/WebSocket connector must satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ..runtime_contract import (
    ACTOR_KINDS,
    DATA_PLANE_ACTIONS,
    ENDPOINT_ROLE_CAPABILITIES,
    ENDPOINT_ROLES,
    OUTBOUND_REQUESTS,
    RAW_ACTIONS,
    RENDER_PLACEMENTS,
    RUNTIME_PROTOCOL_VERSION,
    RuntimeEnvelope,
    _non_empty_str,
    action_of,
    category_of,
    validate_envelope_shape,
)

_REMOTE_CLIENT_ROLES = frozenset({"browser-client", "qt-client"})
_PROJECTION_CAPABILITIES = frozenset({"render", "workbench"})


@dataclass(frozen=True)
class EndpointRegistration:
    endpoint_id: str
    role: str
    capabilities: frozenset[str]
    actor_id: str | None = None
    actor_kind: str | None = None


@dataclass(frozen=True)
class SessionRouteResult:
    status: str  # accepted | duplicate | rejected
    message: Mapping[str, Any] | None = None
    envelope: RuntimeEnvelope | None = None
    recipient_endpoint_ids: tuple[str, ...] = ()
    reason: str | None = None
    detail: str | None = None


class SessionRuntimeRouter:
    """Validate one single-authority remote session.

    One instance belongs to one viewer and one immutable live session. The
    Python endpoint is registered at construction. RRS0 permits at most one
    remote human client and, for server rendering, one render worker.
    """

    def __init__(
        self,
        viewer_id: str,
        session_id: str,
        *,
        render_on: str,
        max_processed_commands: int = 1024,
    ) -> None:
        if not _non_empty_str(viewer_id):
            raise ValueError("viewer_id must be a non-empty string")
        if not _non_empty_str(session_id):
            raise ValueError("session_id must be a non-empty string")
        if render_on not in RENDER_PLACEMENTS:
            raise ValueError("render_on must be 'client' or 'server'")
        if not isinstance(max_processed_commands, int) or isinstance(max_processed_commands, bool):
            raise ValueError("max_processed_commands must be a positive integer")
        if max_processed_commands < 1:
            raise ValueError("max_processed_commands must be a positive integer")

        self.viewer_id = viewer_id
        self.session_id = session_id
        self.render_on = render_on
        self.python_endpoint = f"python:{viewer_id}"
        self._max_processed_commands = max_processed_commands
        self._processed_commands: dict[str, None] = {}
        self._message_counter = 0
        self._endpoints: dict[str, EndpointRegistration] = {
            self.python_endpoint: EndpointRegistration(
                endpoint_id=self.python_endpoint,
                role="python",
                capabilities=frozenset({"authority"}),
                actor_id=self.python_endpoint,
                actor_kind="system",
            )
        }

    @property
    def endpoints(self) -> tuple[EndpointRegistration, ...]:
        return tuple(self._endpoints.values())

    def register_endpoint(
        self,
        endpoint_id: str,
        role: str,
        capabilities: Iterable[str],
        *,
        actor_id: str | None = None,
        actor_kind: str | None = None,
    ) -> EndpointRegistration:
        if not _non_empty_str(endpoint_id):
            raise ValueError("endpoint_id must be a non-empty string")
        if endpoint_id in self._endpoints:
            raise ValueError(f"endpoint already registered: {endpoint_id}")
        if role not in ENDPOINT_ROLES:
            raise ValueError(f"unknown endpoint role: {role}")
        if role == "python":
            raise ValueError("the Python authority endpoint is registered by the session")
        if isinstance(capabilities, (str, bytes)):
            raise ValueError("capabilities must be an iterable of capability names")
        capability_set = frozenset(capabilities)
        if any(not _non_empty_str(item) for item in capability_set):
            raise ValueError("capabilities contain an invalid name")
        disallowed = capability_set - ENDPOINT_ROLE_CAPABILITIES[role]
        if disallowed:
            raise ValueError(f"role {role} may not claim capabilities {sorted(disallowed)}")
        if (actor_id is None) != (actor_kind is None):
            raise ValueError("actor_id and actor_kind must be declared together")
        if actor_id is not None and not _non_empty_str(actor_id):
            raise ValueError("actor_id must be a non-empty string")
        if actor_kind is not None and actor_kind not in ACTOR_KINDS:
            raise ValueError(f"unknown actor_kind: {actor_kind}")

        self._validate_role_contract(role, capability_set, actor_id, actor_kind)
        registration = EndpointRegistration(
            endpoint_id=endpoint_id,
            role=role,
            capabilities=capability_set,
            actor_id=actor_id,
            actor_kind=actor_kind,
        )
        self._endpoints[endpoint_id] = registration
        return registration

    def _validate_role_contract(
        self,
        role: str,
        capabilities: frozenset[str],
        actor_id: str | None,
        actor_kind: str | None,
    ) -> None:
        if role in _REMOTE_CLIENT_ROLES:
            if any(item.role in _REMOTE_CLIENT_ROLES for item in self._endpoints.values()):
                raise ValueError("a remote human client is already registered")
            required = {"command-origin", "input-send", "workbench"}
            if role == "qt-client":
                required.add("native-host")
            if self.render_on == "client":
                required.update({"render", "structure-receive"})
                forbidden = {"video-receive"}
            else:
                required.add("video-receive")
                forbidden = {"render", "structure-receive"}
            self._require_capabilities(role, capabilities, required, forbidden)
            if actor_kind != "human" or actor_id is None:
                raise ValueError(f"role {role} requires a human actor")
            return

        if role == "render-worker":
            if self.render_on != "server":
                raise ValueError("a render worker is invalid when render_on='client'")
            if any(item.role == "render-worker" for item in self._endpoints.values()):
                raise ValueError("a render worker is already registered")
            required = {"input-receive", "render", "structure-receive", "video-send"}
            self._require_capabilities(role, capabilities, required, set())
            if actor_kind != "system" or actor_id is None:
                raise ValueError("role render-worker requires a system actor")
            return

        if role == "agent":
            self._require_capabilities(role, capabilities, {"command-origin"}, set())
            if actor_kind != "agent" or actor_id is None:
                raise ValueError("role agent requires an agent actor")

    @staticmethod
    def _require_capabilities(
        role: str,
        capabilities: frozenset[str],
        required: set[str],
        forbidden: set[str],
    ) -> None:
        missing = required - capabilities
        if missing:
            raise ValueError(f"role {role} is missing capabilities {sorted(missing)}")
        present_forbidden = forbidden & capabilities
        if present_forbidden:
            raise ValueError(
                f"role {role} may not activate capabilities {sorted(present_forbidden)} "
                "for this rendering placement"
            )

    def unregister_endpoint(self, endpoint_id: str) -> bool:
        if endpoint_id == self.python_endpoint:
            raise ValueError("the Python authority endpoint cannot be unregistered")
        return self._endpoints.pop(endpoint_id, None) is not None

    def endpoint(self, endpoint_id: str) -> EndpointRegistration | None:
        return self._endpoints.get(endpoint_id)

    def route_inbound(self, value: Any) -> SessionRouteResult:
        envelope = validate_envelope_shape(value)
        if envelope is None:
            return self._rejected("malformed-envelope", "Runtime envelope is malformed")
        if envelope.protocol_version != RUNTIME_PROTOCOL_VERSION:
            return self._rejected(
                "protocol-mismatch", f"Unsupported protocol {envelope.protocol_version}"
            )
        if envelope.viewer_id != self.viewer_id:
            return self._rejected(
                "viewer-mismatch", f"Envelope belongs to viewer {envelope.viewer_id}"
            )
        if envelope.session_id != self.session_id:
            return self._rejected(
                "session-mismatch", f"Envelope belongs to session {envelope.session_id}"
            )
        source = self._endpoints.get(envelope.endpoint_id)
        if source is None or source.role == "python":
            return self._rejected(
                "unknown-source", f"Unexpected source endpoint {envelope.endpoint_id}"
            )
        if envelope.target_endpoint_id not in (None, self.python_endpoint):
            return self._rejected(
                "unknown-target", f"Unexpected target endpoint {envelope.target_endpoint_id}"
            )
        if envelope.actor_id != source.actor_id or envelope.actor_kind != source.actor_kind:
            return self._rejected(
                "actor-mismatch", f"Envelope actor does not own endpoint {source.endpoint_id}"
            )

        action = envelope.action
        if action in RAW_ACTIONS or action in DATA_PLANE_ACTIONS:
            return self._rejected("not-enveloped", f"Action {action} must not be enveloped")
        if action in OUTBOUND_REQUESTS:
            return self._rejected("outbound-only", f"Action {action} is Python-originated only")
        category = category_of(action)
        if category is None:
            return self._rejected("unknown-action", f"Unknown runtime action {action}")
        if envelope.direction != category:
            return self._rejected(
                "direction-mismatch",
                f"Action {action} is {category} but envelope declares {envelope.direction}",
            )
        if category in {"command", "request"} and "command-origin" not in source.capabilities:
            return self._rejected(
                "capability-mismatch", f"Endpoint {source.endpoint_id} may not originate commands"
            )
        if not isinstance(envelope.payload, Mapping):
            return self._rejected("malformed-payload", f"Action {action} payload is not a mapping")
        if envelope.payload.get("event") != action:
            return self._rejected(
                "action-payload-mismatch",
                f"Envelope action {action} does not match payload event "
                f"{envelope.payload.get('event')!r}",
            )

        if category == "command":
            if envelope.message_id in self._processed_commands:
                return SessionRouteResult(
                    "duplicate",
                    message=envelope.payload,
                    envelope=envelope,
                )
            self._record_command(envelope.message_id)

        return SessionRouteResult(
            "accepted",
            message=envelope.payload,
            envelope=envelope,
            recipient_endpoint_ids=(self.python_endpoint,),
        )

    def wrap_outbound(
        self,
        message: Mapping[str, Any],
        *,
        target_endpoint_id: str | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        operation_id: str | None = None,
        deadline_unix_ms: int | None = None,
    ) -> dict[str, Any]:
        action = action_of(message)
        if action is None:
            raise ValueError("outbound message has no action")
        if action in RAW_ACTIONS or action in DATA_PLANE_ACTIONS:
            raise ValueError(f"action {action} belongs to a separate transport plane")
        if target_endpoint_id is not None:
            target = self._endpoints.get(target_endpoint_id)
            if target is None or target.role == "python":
                raise ValueError(f"unknown outbound target endpoint: {target_endpoint_id}")
        direction = "request" if action in OUTBOUND_REQUESTS else "projection"
        self._message_counter += 1
        envelope: dict[str, Any] = {
            "protocolVersion": RUNTIME_PROTOCOL_VERSION,
            "viewerId": self.viewer_id,
            "sessionId": self.session_id,
            "endpointId": self.python_endpoint,
            "messageId": f"py-{self.session_id}-{self._message_counter}",
            "direction": direction,
            "action": action,
            "payload": message,
            "actorId": self.python_endpoint,
            "actorKind": "system",
        }
        optional = {
            "targetEndpointId": target_endpoint_id,
            "correlationId": correlation_id,
            "causationId": causation_id,
            "operationId": operation_id,
            "deadlineUnixMs": deadline_unix_ms,
        }
        envelope.update({key: value for key, value in optional.items() if value is not None})
        if validate_envelope_shape(envelope) is None:
            raise ValueError("outbound envelope metadata is malformed")
        return envelope

    def duplicate_ack(self, command: RuntimeEnvelope) -> dict[str, Any]:
        """Build the observable acknowledgement for a deduplicated command."""
        if command.endpoint_id not in self._endpoints:
            raise ValueError(f"unknown command endpoint: {command.endpoint_id}")
        self._message_counter += 1
        return {
            "protocolVersion": RUNTIME_PROTOCOL_VERSION,
            "viewerId": self.viewer_id,
            "sessionId": self.session_id,
            "endpointId": self.python_endpoint,
            "targetEndpointId": command.endpoint_id,
            "messageId": f"py-{self.session_id}-{self._message_counter}",
            "correlationId": command.message_id,
            "causationId": command.message_id,
            "operationId": command.operation_id or command.message_id,
            "direction": "ack",
            "action": "command_duplicate_ack",
            "payload": {
                "event": "command_duplicate_ack",
                "message_id": command.message_id,
            },
            "actorId": self.python_endpoint,
            "actorKind": "system",
        }

    def correlated_projection(
        self,
        request: RuntimeEnvelope,
        action: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Answer an accepted client request on that client's exact endpoint."""
        if request.endpoint_id not in self._endpoints:
            raise ValueError(f"unknown request endpoint: {request.endpoint_id}")
        self._message_counter += 1
        return {
            "protocolVersion": RUNTIME_PROTOCOL_VERSION,
            "viewerId": self.viewer_id,
            "sessionId": self.session_id,
            "endpointId": self.python_endpoint,
            "targetEndpointId": request.endpoint_id,
            "messageId": f"py-{self.session_id}-{self._message_counter}",
            "correlationId": request.message_id,
            "direction": "projection",
            "action": action,
            "payload": dict(payload),
            "actorId": self.python_endpoint,
            "actorKind": "system",
        }

    def projection_endpoint_ids(self) -> tuple[str, ...]:
        return tuple(
            item.endpoint_id
            for item in self._endpoints.values()
            if item.role != "python" and item.capabilities & _PROJECTION_CAPABILITIES
        )

    def rendering_endpoint_ids(self) -> tuple[str, ...]:
        return tuple(
            item.endpoint_id
            for item in self._endpoints.values()
            if item.role != "python" and "render" in item.capabilities
        )

    def _record_command(self, message_id: str) -> None:
        self._processed_commands[message_id] = None
        while len(self._processed_commands) > self._max_processed_commands:
            oldest = next(iter(self._processed_commands))
            del self._processed_commands[oldest]

    @staticmethod
    def _rejected(reason: str, detail: str) -> SessionRouteResult:
        return SessionRouteResult("rejected", reason=reason, detail=detail)
