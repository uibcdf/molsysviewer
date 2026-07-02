from __future__ import annotations


from smonitor import signal


class InteractionMixin:
    @signal(tags=["interaction", "query"])
    def get_last_hover_event(self) -> dict | None:
        if self._last_hover_event is None:
            return None
        return dict(self._last_hover_event)

    @signal(tags=["interaction", "query"])
    def get_last_click_event(self) -> dict | None:
        if self._last_click_event is None:
            return None
        return dict(self._last_click_event)

    @signal(tags=["interaction", "query"])
    def get_last_context_event(self) -> dict | None:
        if self._last_context_event is None:
            return None
        return dict(self._last_context_event)

    @signal(tags=["interaction", "query"])
    def get_last_context_action_event(self) -> dict | None:
        if self._last_context_action_event is None:
            return None
        return dict(self._last_context_action_event)

    @signal(tags=["interaction", "query"])
    def get_last_active_selection_event(self) -> dict | None:
        if self._last_active_selection_event is None:
            return None
        return dict(self._last_active_selection_event)

    @signal(tags=["interaction", "query"])
    def get_last_tool_state_event(self) -> dict | None:
        if self._last_tool_state_event is None:
            return None
        return dict(self._last_tool_state_event)

    @signal(tags=["interaction", "query"])
    def get_last_measurement_created_event(self) -> dict | None:
        if self._last_measurement_created_event is None:
            return None
        return dict(self._last_measurement_created_event)

    def on_hover(self, callback) -> None:
        """Register a callback invoked on every ``interaction_hover`` event.

        The callback receives the event dict as its only argument.  The dict
        always contains ``event`` and ``kind`` keys; when ``kind`` is
        ``"structure"``, ``"annotation"``, or ``"measurement"`` it also
        contains ``atom_indices`` and, for the latter two, ``tag``.

        Call :meth:`off_hover` with the same callable to unregister.
        """
        if callback not in self._hover_callbacks:
            self._hover_callbacks.append(callback)

    def off_hover(self, callback) -> None:
        """Remove a previously registered hover callback."""
        try:
            self._hover_callbacks.remove(callback)
        except ValueError:
            pass

    def on_click(self, callback) -> None:
        """Register a callback invoked on every ``interaction_click`` event.

        The callback receives the event dict as its only argument.

        Call :meth:`off_click` with the same callable to unregister.
        """
        if callback not in self._click_callbacks:
            self._click_callbacks.append(callback)

    def off_click(self, callback) -> None:
        """Remove a previously registered click callback."""
        try:
            self._click_callbacks.remove(callback)
        except ValueError:
            pass

    def on_context(self, callback) -> None:
        """Register a callback invoked on every ``interaction_context_menu`` event.

        The callback receives the event dict as its only argument.

        Call :meth:`off_context` with the same callable to unregister.
        """
        if callback not in self._context_callbacks:
            self._context_callbacks.append(callback)

    def off_context(self, callback) -> None:
        """Remove a previously registered context-menu callback."""
        try:
            self._context_callbacks.remove(callback)
        except ValueError:
            pass

    def on_frame_change(self, callback) -> None:
        """Register a callback invoked whenever the trajectory frame changes.

        The callback receives an event dict with ``event`` (``"frame_changed"``),
        ``frame`` (the 0-based original-structure index) and ``is_playing``.
        Useful to drive synchronized views such as the 2D trajectory plot.

        Call :meth:`off_frame_change` with the same callable to unregister.
        """
        if callback not in self._frame_change_callbacks:
            self._frame_change_callbacks.append(callback)

    def off_frame_change(self, callback) -> None:
        """Remove a previously registered frame-change callback."""
        try:
            self._frame_change_callbacks.remove(callback)
        except ValueError:
            pass


InteractionMixin.__module__ = "molsysviewer.viewer"
for _name, _value in InteractionMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass

