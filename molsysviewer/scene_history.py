from __future__ import annotations

import json
import warnings
from contextlib import contextmanager
from functools import wraps
from typing import Any


def _history_operation_key(
    self: Any,
    fn_name: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[str, str, str]:
    """Return the stable identity used to coalesce repeated mutations."""
    class_name = type(self).__name__
    kind = "layer" if class_name in {"Layer", "LayersManager"} else getattr(self, "kind", None)
    if not isinstance(kind, str) or not kind:
        kind = {
            "AnnotationsManager": "annotation",
            "MeasurementsManager": "measurement",
            "RegionsManager": "region",
            "ShapesManager": "shape",
            "Whole": "whole",
        }.get(class_name, class_name.lower())
        if class_name.endswith("Shapes"):
            kind = "shape"

    tag = getattr(self, "tag", None)
    if not isinstance(tag, str):
        candidate = kwargs.get("tag", args[0] if args else None)
        tag = candidate if isinstance(candidate, str) else ""
    return kind, tag, fn_name


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
        history._begin_operation(_history_operation_key(self, fn.__name__, args, kwargs))  # noqa: SLF001
        try:
            return fn(self, *args, **kwargs)
        finally:
            history._end_operation()  # noqa: SLF001
    return wrapper


class SceneHistory:
    """The single scene-level undo/redo history (Contract H, Decision B1).

    Snapshot-based: before each mutating public operation a full ``export_state``
    snapshot is encoded as compact JSON bytes; :meth:`undo` restores the
    previous snapshot via ``import_state`` and :meth:`redo` re-applies. The
    undo/redo store is bounded by both entry count and encoded byte size. There
    is exactly one history per view, and it absorbs what used to be a separate
    frontend selection undo/redo — the active selection is part of the
    serialised snapshot.

    It is session-scoped and is **not** itself serialised; it is invalidated on
    load and on ``apply_system_edit`` (the snapshots would reference a stale
    index space).
    """

    def __init__(
        self,
        view: Any,
        *,
        limit: int = 25,
        byte_limit: int = 64 * 1024 * 1024,
    ) -> None:
        self._view = view
        self._limit = limit
        self._byte_limit = max(1, int(byte_limit))
        self._undo: list[bytes] = []
        self._redo: list[bytes] = []
        self._undo_bytes = 0
        self._redo_bytes = 0
        self._budget_warning_emitted = False
        self._depth = 0
        self._suspended = False
        self._coalescing_depth = 0
        self._coalesced_keys: set[tuple[str, str, str]] = set()

    # ── Auto-checkpoint hooks (used by the records-history decorator) ──────

    def _begin_operation(self, operation_key: tuple[str, str, str]) -> None:
        """Snapshot the pre-operation state, once, for the outermost mutating op."""
        if self._suspended:
            return
        if self._depth == 0:
            already_coalesced = self._coalescing_depth > 0 and operation_key in self._coalesced_keys
            if not already_coalesced:
                snapshot = self._encode(self._view.export_state())
                # Skip a redundant checkpoint when the previous operation left the
                # scene unchanged (e.g. a validation that raised, or a no-op call),
                # so undo never lands on an identical state.
                if not self._undo or self._undo[-1] != snapshot:
                    self._undo.append(snapshot)
                    self._undo_bytes += len(snapshot)
                    if len(self._undo) > self._limit:
                        self._undo_bytes -= len(self._undo.pop(0))
                self._redo_bytes = 0
                self._redo.clear()
                self._enforce_byte_limit()
                if self._coalescing_depth > 0:
                    self._coalesced_keys.add(operation_key)
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
        current = self._encode(self._view.export_state())
        snapshot = self._undo.pop()
        self._undo_bytes -= len(snapshot)
        self._redo.append(current)
        self._redo_bytes += len(current)
        self._restore(snapshot)
        self._enforce_byte_limit()
        self._notify_state()
        return True

    def redo(self) -> bool:
        """Re-apply the operation most recently undone."""
        if not self._redo:
            return False
        current = self._encode(self._view.export_state())
        snapshot = self._redo.pop()
        self._redo_bytes -= len(snapshot)
        self._undo.append(current)
        self._undo_bytes += len(current)
        self._restore(snapshot)
        self._enforce_byte_limit()
        self._notify_state()
        return True

    def clear(self) -> None:
        """Drop the whole history (called on load and on system edits)."""
        self._undo.clear()
        self._redo.clear()
        self._undo_bytes = 0
        self._redo_bytes = 0
        self._budget_warning_emitted = False
        self._depth = 0
        self._coalescing_depth = 0
        self._coalesced_keys.clear()
        self._notify_state()

    def begin_coalescing(self) -> None:
        """Open a window that records one checkpoint per object operation."""
        if self._coalescing_depth == 0:
            self._coalesced_keys.clear()
        self._coalescing_depth += 1

    def end_coalescing(self) -> None:
        """Close a coalescing window opened by :meth:`begin_coalescing`."""
        if self._coalescing_depth == 0:
            return
        self._coalescing_depth -= 1
        if self._coalescing_depth == 0:
            self._coalesced_keys.clear()
            self._notify_state()

    @contextmanager
    def coalescing(self):
        """Coalesce repeated mutations while preserving distinct operations."""
        self.begin_coalescing()
        try:
            yield self
        finally:
            self.end_coalescing()

    @contextmanager
    def suspended(self):
        """Suspend checkpoint creation while rebuilding a scene."""
        was_suspended = self._suspended
        self._suspended = True
        try:
            yield was_suspended
        finally:
            self._suspended = was_suspended

    @staticmethod
    def _encode(snapshot: dict) -> bytes:
        return json.dumps(
            snapshot,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @staticmethod
    def _decode(snapshot: bytes) -> dict:
        return json.loads(snapshot.decode("utf-8"))

    def _enforce_byte_limit(self) -> None:
        evicted = 0
        while self._undo_bytes + self._redo_bytes > self._byte_limit:
            if len(self._undo) > 1:
                self._undo_bytes -= len(self._undo.pop(0))
            elif len(self._redo) > 1:
                self._redo_bytes -= len(self._redo.pop(0))
            else:
                break
            evicted += 1
        over_budget = self._undo_bytes + self._redo_bytes > self._byte_limit
        if (evicted or over_budget) and not self._budget_warning_emitted:
            budget_mib = self._byte_limit / (1024 * 1024)
            warnings.warn(
                f"Scene history exceeded its {budget_mib:g} MiB storage budget; "
                "oldest undo/redo checkpoints were discarded where possible while "
                "preserving the current scene and newest checkpoint.",
                RuntimeWarning,
                stacklevel=3,
            )
            self._budget_warning_emitted = True

    def _restore(self, snapshot: bytes) -> None:
        # Suspend checkpointing so import_state's own mutations do not push
        # new history entries.
        with self.suspended():
            self._view.import_state(self._decode(snapshot))
