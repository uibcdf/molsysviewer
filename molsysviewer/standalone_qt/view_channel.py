"""A widget-like transport that backs a persistent MolSysView with the Qt bridge.

In Jupyter the `MolSysView` talks to the frontend through an AnyWidget
(`view.widget`): `widget.send(...)` for outgoing messages, `widget.on_msg(...)`
for incoming events, and synced traits for config + `initial_messages` for the
pre-ready queue.

In the Qt standalone there is no AnyWidget. `QtViewChannel` implements the small
subset of that interface the view actually uses, routing outgoing messages
through the `QtMessageBridge` and delivering the bridge's product events back to
the view's `on_msg` handler. This lets the *same* MolSysView drive the Qt shell,
so loads, rebuilds, interactions and movie export all work like in Jupyter.
"""

from __future__ import annotations

from typing import Any, Callable


class _Layout:
    """Stub for `widget.layout` (the Jupyter DOMWidget layout object)."""

    def __init__(self) -> None:
        self.height: Any = None
        self.width: Any = None
        self.min_height: Any = None


class QtViewChannel:
    def __init__(self, bridge) -> None:
        self._bridge = bridge
        self._msg_callbacks: list[Callable[..., Any]] = []
        self._forwarded_initial: list[dict] = []
        self._initial_messages: list[dict] = []
        self.layout = _Layout()

        # Config is baked into the shell HTML at build time; kept here as plain
        # settable attributes so the view can assign them without error (inert).
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
        self.model_id = "molsysviewer-qt"
        self._model_name = "MolSysViewerModel"
        self._model_module = "molsysviewer"
        self._model_module_version = ""

        # Deliver the bridge's product events to on_msg subscribers.
        bridge.event_sink = self._dispatch_event

    # -- outgoing (Python -> JS) ---------------------------------------------

    def send(self, msg: dict, buffers: Any = None) -> None:
        self._bridge.send(dict(msg))

    @property
    def initial_messages(self) -> list[dict]:
        return self._initial_messages

    @initial_messages.setter
    def initial_messages(self, value) -> None:
        # The view sets this to the *cumulative* pending list before `ready`.
        # Forward only the newly-appended messages to the bridge (which queues
        # them until the frontend is ready), each exactly once.
        value = list(value or [])
        for msg in value[len(self._forwarded_initial):]:
            self._bridge.send(dict(msg))
        self._forwarded_initial = value
        self._initial_messages = value

    # -- incoming (JS -> Python) ---------------------------------------------

    def on_msg(self, callback: Callable[..., Any]) -> None:
        self._msg_callbacks.append(callback)

    def _dispatch_event(self, event: dict) -> None:
        # AnyWidget's on_msg signature is (widget, content, buffers).
        for callback in list(self._msg_callbacks):
            callback(self, event, [])

    # -- Jupyter display protocol (unused in Qt; benign stubs) ---------------

    def get_state(self, *args: Any, **kwargs: Any) -> dict:
        return {}


__all__ = ["QtViewChannel"]
