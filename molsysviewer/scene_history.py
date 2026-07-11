from __future__ import annotations

from functools import wraps
from typing import Any


def records_scene_history(fn):
    """Wrap a mutating public method so it checkpoints the scene history.

    The outermost decorated call in a nested chain takes one pre-operation
    snapshot (a re-entrancy guard lives in :class:`SceneHistory`), so a public
    op that internally calls other decorated ops still yields a single undo
    step. Works on methods of the view, of ``Region`` / ``RegionsManager`` /
    ``Whole`` (found via ``self._view``), i.e. anything reachable to the view's
    ``history``.
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        view = self if hasattr(self, "history") else getattr(self, "_view", None)
        history = getattr(view, "history", None)
        if history is None:
            return fn(self, *args, **kwargs)
        history._begin_operation()  # noqa: SLF001
        try:
            return fn(self, *args, **kwargs)
        finally:
            history._end_operation()  # noqa: SLF001
    return wrapper


class SceneHistory:
    """The single scene-level undo/redo history (Contract H, Decision B1).

    Snapshot-based: before each mutating public operation a full ``export_state``
    snapshot is pushed; :meth:`undo` restores the previous snapshot via
    ``import_state`` and :meth:`redo` re-applies. There is exactly one of these
    per view, and it absorbs what used to be a separate frontend selection
    undo/redo — the active selection is part of the serialised snapshot.

    It is session-scoped and is **not** itself serialised; it is invalidated on
    load and on ``apply_system_edit`` (the snapshots would reference a stale
    index space).
    """

    def __init__(self, view: Any, *, limit: int = 25) -> None:
        self._view = view
        self._limit = limit
        self._undo: list[dict] = []
        self._redo: list[dict] = []
        self._depth = 0
        self._suspended = False

    # ── Auto-checkpoint hooks (used by the records-history decorator) ──────

    def _begin_operation(self) -> None:
        """Snapshot the pre-operation state, once, for the outermost mutating op."""
        if self._suspended:
            return
        if self._depth == 0:
            snapshot = self._view.export_state()
            # Skip a redundant checkpoint when the previous operation left the
            # scene unchanged (e.g. a validation that raised, or a no-op call),
            # so undo never lands on an identical state.
            if not self._undo or self._undo[-1] != snapshot:
                self._undo.append(snapshot)
                if len(self._undo) > self._limit:
                    self._undo.pop(0)
            self._redo.clear()
        self._depth += 1

    def _end_operation(self) -> None:
        if self._suspended:
            return
        self._depth = max(0, self._depth - 1)
        if self._depth == 0:
            self._notify_state()

    def _notify_state(self) -> None:
        """Push can_undo / can_redo to the frontend so the GUI Undo/Redo buttons
        reflect the single scene history (not a separate frontend stack)."""
        send = getattr(self._view, "_send_runtime_only", None)
        if send is None:
            return
        send({
            "op": "set_history_state",
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
        })

    # ── Public API ─────────────────────────────────────────────────────────

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self) -> bool:
        """Restore the scene to before the last mutating operation."""
        if not self._undo:
            return False
        current = self._view.export_state()
        snapshot = self._undo.pop()
        self._redo.append(current)
        self._restore(snapshot)
        self._notify_state()
        return True

    def redo(self) -> bool:
        """Re-apply the operation most recently undone."""
        if not self._redo:
            return False
        current = self._view.export_state()
        snapshot = self._redo.pop()
        self._undo.append(current)
        self._restore(snapshot)
        self._notify_state()
        return True

    def clear(self) -> None:
        """Drop the whole history (called on load and on system edits)."""
        self._undo.clear()
        self._redo.clear()
        self._depth = 0
        self._notify_state()

    def _restore(self, snapshot: dict) -> None:
        # Suspend checkpointing so import_state's own mutations do not push
        # new history entries.
        self._suspended = True
        try:
            self._view.import_state(snapshot)
        finally:
            self._suspended = False
