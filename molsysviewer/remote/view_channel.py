"""Widget-like connector for a future remote session service.

The channel is transport-agnostic: callers inject one control sender and one
binary/data-plane sender. It opens no socket. This keeps ``MolSysView`` reusable
while the HTTP/WebSocket service remains a later RRS slice.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from ..runtime_contract import DATA_PLANE_ACTIONS, RAW_ACTIONS, action_of, is_envelope
from .session_router import SessionRouteResult, SessionRuntimeRouter


class _Layout:
    def __init__(self) -> None:
        self.height: Any = None
        self.width: Any = None
        self.min_height: Any = None


class RemoteViewChannel:
    """The widget-like surface consumed by :class:`MolSysView`.

    ``send_control`` receives a validated RuntimeEnvelope. ``send_data``
    receives raw bootstrap/data-plane messages and their optional binary
    buffers. The split makes silently dropping structural buffers impossible.
    """

    def __init__(
        self,
        send_control: Callable[[Mapping[str, Any]], None],
        *,
        render_on: str,
        send_data: Callable[[Mapping[str, Any], Any], None] | None = None,
    ) -> None:
        if not callable(send_control):
            raise TypeError("send_control must be callable")
        if send_data is not None and not callable(send_data):
            raise TypeError("send_data must be callable")
        if render_on not in {"client", "server"}:
            raise ValueError("render_on must be 'client' or 'server'")
        self._send_control = send_control
        self._send_data = send_data
        self.supports_array_native_buffers = send_data is not None
        self.render_on = render_on
        self._router: SessionRuntimeRouter | None = None
        self._msg_callbacks: list[Callable[..., Any]] = []
        self._runtime_request_callbacks: list[Callable[[Any], Any]] = []
        self._forwarded_initial: list[dict] = []
        self._initial_messages: list[dict] = []
        self._closed = False
        self.download_publisher: Callable[[str, str, bytes], str] | None = None
        self.upload_consumer: Callable[[str, str], Mapping[str, Any]] | None = None
        self.layout = _Layout()

        self.show_controls = True
        self.enable_popout = False
        self.autohide_controls = True
        self.debug_js = False
        self.controls_position = ["top", "right"]
        self.controls_position_fullscreen = ["top", "right"]
        self.controls_mode = "classic"
        self.panel_mode_style = "drawer"
        self.viewer_mode = "integrated"
        self.addon_states: dict = {}
        self.model_id = "molsysviewer-remote"
        self._model_name = "MolSysViewerModel"
        self._model_module = "molsysviewer"
        self._model_module_version = ""

    @property
    def router(self) -> SessionRuntimeRouter:
        if self._router is None:
            raise RuntimeError("remote channel has not been bound to a MolSysView")
        return self._router

    def bind_runtime_identity(self, viewer_id: str, session_id: str) -> None:
        if self._router is not None:
            if self._router.viewer_id == viewer_id and self._router.session_id == session_id:
                return
            raise RuntimeError("remote channel runtime identity is immutable")
        self._router = SessionRuntimeRouter(
            viewer_id,
            session_id,
            render_on=self.render_on,
        )

    def send(self, message: Mapping[str, Any], buffers: Any = None) -> None:
        if self._closed:
            raise RuntimeError("remote channel is closed")
        if is_envelope(message):
            if buffers:
                raise ValueError("runtime envelopes may not carry data-plane buffers")
            self._send_control(message)
            return
        action = action_of(message)
        uses_data_plane = action in RAW_ACTIONS or action in DATA_PLANE_ACTIONS or bool(buffers)
        if uses_data_plane:
            if self._send_data is None:
                raise NotImplementedError(
                    "RemoteViewChannel has no data-plane sender; refusing to drop "
                    f"buffers or raw action {action!r}"
                )
            self._send_data(message, buffers)
            return
        self._send_control(self.router.wrap_outbound(message))

    def receive_control(self, value: Any) -> SessionRouteResult:
        if self._closed:
            return SessionRouteResult(
                "rejected",
                reason="channel-closed",
                detail="Remote channel is closed",
            )
        result = self.router.route_inbound(value)
        if result.status == "accepted":
            if (
                result.envelope is not None
                and result.envelope.action == "request_popup_scene_snapshot"
            ):
                for callback in tuple(self._runtime_request_callbacks):
                    callback(result.envelope)
            else:
                message = result.message
                if (
                    result.envelope is not None
                    and result.envelope.action == "interaction_context_menu"
                    and isinstance(message, Mapping)
                ):
                    message = {
                        **message,
                        "_source_endpoint_id": result.envelope.endpoint_id,
                    }
                for callback in tuple(self._msg_callbacks):
                    callback(self, message, [])
        elif result.status == "duplicate":
            if result.envelope is None:  # pragma: no cover - router invariant
                raise RuntimeError("duplicate route result has no envelope")
            self._send_control(self.router.duplicate_ack(result.envelope))
        return result

    def receive_data(
        self,
        value: Any,
        *,
        source_endpoint_id: str,
    ) -> SessionRouteResult:
        """Accept one authenticated raw/data-plane message from a live endpoint."""
        if self._closed:
            return SessionRouteResult(
                "rejected", reason="channel-closed", detail="Remote channel is closed"
            )
        if not isinstance(value, Mapping):
            return SessionRouteResult(
                "rejected", reason="malformed-data", detail="Data-plane message is not a mapping"
            )
        source = self.router.endpoint(source_endpoint_id)
        if source is None or source.role == "python":
            return SessionRouteResult(
                "rejected",
                reason="unknown-source",
                detail=f"Unexpected source endpoint {source_endpoint_id}",
            )
        action = action_of(value)
        if action not in RAW_ACTIONS and action not in DATA_PLANE_ACTIONS:
            return SessionRouteResult(
                "rejected",
                reason="unknown-data-action",
                detail=f"Action {action!r} does not belong to the raw/data plane",
            )
        viewer_id = value.get("viewer_id")
        session_id = value.get("session_id")
        if viewer_id is not None and viewer_id != self.router.viewer_id:
            return SessionRouteResult(
                "rejected",
                reason="viewer-mismatch",
                detail=f"Message belongs to viewer {viewer_id}",
            )
        if session_id is not None and session_id != self.router.session_id:
            return SessionRouteResult(
                "rejected",
                reason="session-mismatch",
                detail=f"Message belongs to session {session_id}",
            )
        for callback in tuple(self._msg_callbacks):
            callback(self, value, [])
        return SessionRouteResult(
            "accepted",
            message=value,
            recipient_endpoint_ids=(self.router.python_endpoint,),
        )

    def on_msg(self, callback: Callable[..., Any]) -> None:
        if not callable(callback):
            raise TypeError("message callback must be callable")
        self._msg_callbacks.append(callback)

    def on_runtime_request(self, callback: Callable[[Any], Any]) -> None:
        """Register a correlation-preserving transport-request consumer."""
        if not callable(callback):
            raise TypeError("runtime request callback must be callable")
        self._runtime_request_callbacks.append(callback)

    def publish_download(self, filename: str, media_type: str, data: bytes) -> str:
        publisher = self.download_publisher
        if publisher is None:
            raise RuntimeError("remote channel has no download publisher")
        return publisher(filename, media_type, data)

    def consume_upload(self, path: str, filename: str) -> Mapping[str, Any]:
        consumer = self.upload_consumer
        if consumer is None:
            raise RuntimeError("remote channel has no upload consumer")
        return consumer(path, filename)

    @property
    def initial_messages(self) -> list[dict]:
        return self._initial_messages

    @initial_messages.setter
    def initial_messages(self, value) -> None:
        messages = list(value or [])
        for message in messages[len(self._forwarded_initial):]:
            self.send(message)
        self._forwarded_initial = messages
        self._initial_messages = messages

    def get_state(self, *args: Any, **kwargs: Any) -> dict:
        return {}

    def close(self) -> None:
        self._closed = True
        self._msg_callbacks.clear()
        self._runtime_request_callbacks.clear()
        self.upload_consumer = None


__all__ = ["RemoteViewChannel"]
