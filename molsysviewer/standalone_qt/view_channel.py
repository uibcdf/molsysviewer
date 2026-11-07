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

import logging
import math
from asyncio import get_running_loop
from copy import deepcopy
from importlib import import_module
from threading import RLock, get_ident
from typing import Any, Callable

from smonitor.integrations import context_extra, emit_from_catalog
from traitlets import HasTraits

from .._private.smonitor import CATALOG, META, PACKAGE_ROOT
from ..widget import MolSysViewerWidget, _callback_delay, _ScheduledCallback
from .status import _HOST_SHORTCUTS
from .utils import _frontend_event_validation_error

logger = logging.getLogger(__name__)


class _Layout:
    """Stub for `widget.layout` (the Jupyter DOMWidget layout object)."""

    def __init__(self) -> None:
        self.height: Any = None
        self.width: Any = None
        self.min_height: Any = None


class QtViewChannel(HasTraits):
    supports_array_native_buffers = False
    _FRONTEND_TRAITS = (
        "viewer_mode",
        "controls_mode",
        "panel_mode_style",
        "show_controls",
        "autohide_controls",
        "autohide_scope",
        "controls_position",
        "controls_position_fullscreen",
        "addon_states",
    )
    _SYNC_TRAITS = (
        *_FRONTEND_TRAITS,
        "debug_js",
        "enable_popout",
        "has_molecular_system",
        "runtime_viewer_id",
        "runtime_session_id",
    )

    def __init__(self, bridge) -> None:
        super().__init__()
        # Reuse the widget's validators/defaults without creating an AnyWidget,
        # a comm, or a second Python scene owner.
        traits = MolSysViewerWidget.class_traits()
        self.add_traits(**{name: deepcopy(traits[name]) for name in self._SYNC_TRAITS})
        self._bridge = bridge
        self._callbacks_lock = RLock()
        self._scheduled_callbacks = set()
        self._callbacks_closed = False
        self._channel_closed = False
        self._callback_thread_ident = get_ident()
        self._receiving_ui = False
        self._msg_callbacks: list[Callable[..., Any]] = []
        self._forwarded_initial: list[dict] = []
        self._initial_messages: list[dict] = []
        self.layout = _Layout()

        self.enable_popout = False
        self.model_id = "molsysviewer-qt"
        self._model_name = "MolSysViewerModel"
        self._model_module = "molsysviewer"
        self._model_module_version = ""

        # Deliver the bridge's product events to on_msg subscribers.
        self._event_sink = self._dispatch_event
        bridge.event_sink = self._event_sink
        self.observe(self._send_ui_state, names=list(self._SYNC_TRAITS))

    def _send_ui_state(self, change=None) -> None:
        if not self._receiving_ui:
            self._bridge.send({"op": "set_host_ui", "values": {**self.get_state(), "host_shortcuts": _HOST_SHORTCUTS}})

    # -- outgoing (Python -> JS) ---------------------------------------------

    def send(self, msg: dict, buffers: Any = None) -> None:
        """Deliver a control-plane message to the Qt frontend.

        This control channel carries JSON only. Qt structural arrays use the
        separate binary payload-scheme path. Accepting AnyWidget-style
        ``buffers=`` here and dropping them would lose structural data silently,
        so this refuses immediately and observably.
        """
        if buffers:
            emit_from_catalog(
                CATALOG["binary_transport_unsupported"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra=context_extra(
                    caller="molsysviewer.standalone_qt.QtViewChannel.send",
                    operation="qt-control-plane-send",
                    failure_class="binary_transport_unsupported",
                    last_failure_reason=(
                        f"{len(buffers)} buffer(s) for op {msg.get('op')!r} "
                        "cannot cross the Qt control channel; structural binary "
                        "data uses the payload scheme"
                    ),
                ),
            )
            raise NotImplementedError(
                "QtViewChannel does not carry AnyWidget-style buffers and would "
                f"drop {len(buffers)} buffer(s) for op {msg.get('op')!r}. "
                "Structural binary data uses the Qt payload-scheme path "
                "(see devguide/data_plane_architecture.md)."
            )
        self._bridge.send(dict(msg))

    def _send_array_native_reference(self, message, molsys) -> bool:
        """Encode only the owner's current lazy projection, before JSON exists."""
        return self._bridge._send_array_native_load(
            molsys,
            label=message.get("label"),
            multiple_structures=bool(message.get("multiple_structures")),
        )

    @property
    def initial_messages(self) -> list[dict]:
        return self._initial_messages

    @initial_messages.setter
    def initial_messages(self, value) -> None:
        # The view sets this to the *cumulative* pending list before `ready`.
        # Forward only the newly-appended messages to the bridge (which queues
        # them until the frontend is ready), each exactly once.
        value = list(value or [])
        for msg in value[len(self._forwarded_initial) :]:
            self._bridge.send(dict(msg))
        self._forwarded_initial = value
        self._initial_messages = value

    # -- incoming (JS -> Python) ---------------------------------------------

    def on_msg(self, callback: Callable[..., Any]) -> None:
        self._msg_callbacks.append(callback)

    def _schedule_callback(self, delay_seconds, callback):
        """Own one Qt GUI-thread deadline without importing another Qt binding."""
        delay = _callback_delay(delay_seconds, callback)
        if self._callbacks_closed or getattr(self._bridge, "_closed", False):
            raise RuntimeError("The Qt view channel is closed.")
        parent = self._bridge.webview
        if parent is None or not callable(self._bridge.QTimer):
            raise RuntimeError("The Qt view channel has no GUI timer owner.")
        thread = parent.thread()
        is_current = getattr(thread, "isCurrentThread", None)
        if get_ident() != self._callback_thread_ident or (callable(is_current) and not is_current()):
            raise RuntimeError("Qt callbacks must be scheduled on their owning GUI thread.")
        timer = self._bridge.QTimer(parent)
        timer.setSingleShot(True)
        handle = _ScheduledCallback(self._scheduled_callbacks, callback, self._callbacks_lock)

        def cancel_timer():
            timer.stop()
            timer.timeout.disconnect(handle)
            timer.deleteLater()

        try:
            timer.timeout.connect(handle)
            timer.destroyed.connect(handle._timer_closed)
            handle._set_cancel(cancel_timer)
            # Never round a positive deadline down to an earlier Qt tick.
            timer.start(math.ceil(delay * 1000))
        except BaseException:
            handle.cancel()
            raise
        return handle

    def _require_async_capture_host(self):
        """Refuse asyncio that cannot dispatch this native GUI's events.

        The application chooses an integrated loop at startup; a save must not
        install a policy, pump Qt events recursively or appoint a worker loop.
        Ordinary Studio saves use their existing Future/QTimer route instead.
        """
        from ..viewer.frontend_requests import FrontendRequestError

        if self._channel_closed or getattr(self._bridge, "_closed", False):
            raise FrontendRequestError(reason="view_closed")
        loop = get_running_loop()
        binding = getattr(self._bridge.QTimer, "__module__", "").partition(".")[0]
        loop_type = None
        if binding in {"PySide6", "PySide6_uibcdf"}:
            try:
                loop_type = import_module(f"{binding}.QtAsyncio").QAsyncioEventLoop
            except (ImportError, AttributeError):
                pass
        parent = self._bridge.webview
        same_thread = get_ident() == self._callback_thread_ident
        if parent is not None:
            is_current = getattr(parent.thread(), "isCurrentThread", None)
            same_thread = same_thread and (not callable(is_current) or is_current())
        if loop_type is None or not isinstance(loop, loop_type) or not same_thread:
            raise FrontendRequestError(
                "Qt async saves require a QtAsyncio event loop on the owning GUI thread. "
                "Use an explicitly application-owned integrated loop, or Save in Studio. "
                "Ordinary asyncio.run() does not dispatch Qt events; native GUI lifetime and "
                "shutdown must remain under the application's ownership.",
                reason="qt_async_host_unsupported",
            )

    def close(self) -> None:
        """Detach callbacks and the bridge event sink owned by this channel."""
        if self._channel_closed:
            return
        with self._callbacks_lock:
            self._callbacks_closed = True
            for handle in tuple(self._scheduled_callbacks):
                handle.cancel()
        self._msg_callbacks.clear()
        self.unobserve(self._send_ui_state, names=list(self._SYNC_TRAITS))
        if getattr(self._bridge, "event_sink", None) is self._event_sink:
            self._bridge.event_sink = None
        self._channel_closed = True

    def _dispatch_event(self, event: Any) -> bool:
        validation_error = _frontend_event_validation_error(event)
        if validation_error is not None:
            reject = getattr(self._bridge, "reject_frontend_event", None)
            if callable(reject):
                reject(
                    event,
                    source="Qt view channel",
                    reason=validation_error,
                )
            else:
                logger.warning(
                    "Rejected malformed Qt view-channel event: %s; payload=%r",
                    validation_error,
                    event,
                )
            return False
        if event.get("event") == "qt_ui_state":
            values = event.get("values")
            if not isinstance(values, dict) or set(values) - set(self._FRONTEND_TRAITS):
                raise ValueError("Qt UI state must contain only supported canvas/addon preferences.")
            validated = {name: self.traits()[name].validate(self, value) for name, value in values.items()}
            self._receiving_ui = True
            try:
                for name, value in validated.items():
                    setattr(self, name, value)
            finally:
                self._receiving_ui = False
            return True
        # AnyWidget's on_msg signature is (widget, content, buffers).
        for callback in list(self._msg_callbacks):
            callback(self, event, [])
        return True

    # -- Jupyter display protocol (unused in Qt; benign stubs) ---------------

    def get_state(self, *args: Any, **kwargs: Any) -> dict:
        return {name: deepcopy(getattr(self, name)) for name in self._SYNC_TRAITS}


__all__ = ["QtViewChannel"]
