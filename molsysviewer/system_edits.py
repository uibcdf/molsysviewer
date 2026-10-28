"""Coordinate provider-owned scientific edits with the view's scene projection.

This is an integration service, not a molecular editing engine or molecular Undo.
Providers supply reviewed execution and correspondence; the host owns scene retry.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from numbers import Integral
from threading import RLock
from uuid import uuid4
from weakref import ref

from smonitor import signal

from ._private.argdigest import digest
from ._private.structure_correspondence import normalize_structure_index_map, prepare_structure_edit

_INTERNAL = ContextVar("molsysviewer_system_edit_internal", default=None)


class SystemEditPendingError(RuntimeError):
    """A scene command would use the index space preceding a managed edit."""


class SystemEditSyncError(RuntimeError):
    """Science completed; retry synchronization, never the scientific operation."""

    def __init__(self, operation_id, scientific_result):
        super().__init__("The molecular edit completed, but the scene update failed. Call sync_view() to retry.")
        self.science_completed = True
        self.operation_id = operation_id
        self.scientific_result = scientific_result


@contextmanager
def _scene_call_guard(args, kwargs, name):
    """Guard before digestion/history so skip_digestion cannot bypass ownership."""
    for owner in (*args[:2], kwargs.get("view")):
        fields = getattr(owner, "__dict__", {})
        view = owner if "_system_edits" in fields else fields.get("_view")
        manager = getattr(view, "__dict__", {}).get("_system_edits")
        if manager is None or isinstance(owner, SystemEditsManager):
            continue
        if _INTERNAL.get() is manager:
            yield
            return
        camera_only = type(owner).__module__ == "molsysviewer.viewer.camera" and name in {
            "reset",
            "get_snapshot",
            "set_snapshot",
            "set_mode",
        }
        management = type(owner).__module__ == "molsysviewer.addons" and name not in {
            "build_context_items",
            "refresh_context_items",
            "handle_context_action",
            "resolve_panel_widget",
        }
        with manager._locked():
            if name == "close" and owner is view:
                with manager._internal():
                    yield
                return
            if manager._blocked() and not (camera_only or management):
                raise SystemEditPendingError(manager._reason())
            yield
        return
    yield


# Only scene-owned metadata is copied. Molecular domains, analysis arrays, widget
# resources and arbitrary user extension attributes never enter this checkpoint.
_VIEW_FIELDS = (
    "_shape_history",
    "_annotation_history",
    "_measurement_history",
    "_selection_history",
    "_scene_look",
    "_atom_color_layers",
    "_atom_color_map",
    "_load_blocks",
    "_load_structure_count",
    "_empty",
    "_current_structure_index",
    "_box_record",
    "_box_visible",
    "_last_active_selection_event",
    "_active_selection_recipe",
    "_player_state",
    "_last_label",
    "_region_order_counter",
)
_HANDLE_FIELDS = (
    "_active",
    "_hidden",
    "_enabled",
    "_show_only",
    "_atom_indices",
    "_provenance",
    "_mode",
    "_representation",
    "_preset",
    "_repr_params",
    "order",
    "broken",
    "broken_reason",
    "_filter",
    "selection",
    "_color_scheme",
)
_REGISTRIES = ("_regions", "_layers", "_scene_objects", "_selections")


class _SceneCheckpoint:
    def __init__(self, view):
        self.values = {name: deepcopy(getattr(view, name)) for name in _VIEW_FIELDS}
        self.registries = {name: dict(getattr(view, name)) for name in _REGISTRIES}
        handles = [view.whole, *(obj for registry in self.registries.values() for obj in registry.values())]
        self.handles = [
            (obj, {name: deepcopy(vars(obj)[name]) for name in _HANDLE_FIELDS if name in vars(obj)})
            for obj in {id(obj): obj for obj in handles}.values()
        ]

    def restore(self, view):
        for name, value in self.values.items():
            setattr(view, name, deepcopy(value))
        for name, values in self.registries.items():
            registry = getattr(view, name)
            dict.clear(registry)
            dict.update(registry, values)
        for obj, values in self.handles:
            for name in _HANDLE_FIELDS:
                if name in values:
                    setattr(obj, name, deepcopy(values[name]))
                else:
                    vars(obj).pop(name, None)
            if hasattr(obj, "_payload_key"):
                obj._payload_key = None
        view._invalidate_system_identity()
        view._clear_dynamic_region_cache()


class SystemEditsManager:
    """Per-view integration service at ``view.addons.manager.system_edits``.

    Only reviewed provider adapters should call execute. It receives a read-only
    preparation callback(target), returning a dict with a native ``run`` callable,
    ``changed`` boolean, optional retained atom/structure maps, an interaction
    policy and optional ``failure_atomic`` declaration. Maps describe this one
    operation, not the original scene. The explicit axis_growth capability
    receives native prefix-preserving additions with an added_count plan field.
    Counts validate that declared contract; they never establish correspondence.
    """

    def __init__(self, view):
        self._view_ref = ref(view)
        self._lock = RLock()
        self._state = "synchronized"
        self._operation_id = None
        self._revision = 0
        self._integrated = 0
        self._pending = 0
        self._target = None
        self._checkpoint = None
        self._atoms = None
        self._frames = None
        self._policy = "preserve"
        self._detail = None

    @contextmanager
    def _locked(self):
        if not self._lock.acquire(blocking=False):
            raise SystemEditPendingError("Another operation is updating this view; retry after it completes.")
        try:
            yield
        finally:
            self._lock.release()

    @contextmanager
    def _internal(self):
        token = _INTERNAL.set(self)
        try:
            yield
        finally:
            _INTERNAL.reset(token)

    def _view(self):
        view = self._view_ref()
        if view is None or view.closed:
            raise RuntimeError("System edits cannot operate on a closed view.")
        return view

    def _blocked(self):
        return self._state != "synchronized"

    def _reason(self):
        return self._detail or "Update the view before using scene selections or commands."

    def _message(self):
        return {"op": "set_system_sync_state", **self.get_status(skip_digestion=True)}

    def _notify(self, view):
        # Delivery cannot change scientific completion. A reconnect receives the
        # same state; the normal transport owns endpoint delivery/acknowledgement.
        try:
            if view._ready:
                view._transmit_widget_message(self._message())
        except Exception as exc:
            from ._private.smonitor_emit import emit_suppressed_exception

            emit_suppressed_exception("SystemEditsManager.state_delivery", exc)

    @signal(tags=["edit"])
    @digest()
    def read(self, callback, *, skip_digestion=False):
        """Call a provider reader on the current target under the edit lock.

        Pending edits are already scientific data and can be read. The callback
        must not mutate the target or perform a scene action. It returns its
        native result without adopting independent outputs or copying arrays.
        """
        with self._locked():
            view = self._view()
            if self._state in {"editing", "syncing"}:
                raise SystemEditPendingError("The target is currently being updated.")
            if view.molsys is None:
                raise ValueError("Load a molecular system before reading it.")
            return callback(view.molsys)

    @signal(tags=["edit"])
    @digest()
    def get_status(self, *, skip_digestion=False):
        """Return detached bounded integration metadata, without scientific arrays."""
        with self._locked():
            view = self._view_ref()
            return {
                "state": "closed" if view is None or view.closed else self._state,
                "operation_id": self._operation_id,
                "target_revision": self._revision,
                "integration_revision": self._integrated,
                "pending_operations": self._pending,
                "reason": self._detail,
            }

    def _prepare_maps(self, view, target, plan, axis_growth):
        atoms = plan.get("atom_index_map")
        count = int(target.get_n_atoms())
        if atoms is not None:
            if (
                not isinstance(atoms, dict)
                or any(
                    isinstance(i, bool) or not isinstance(i, Integral) or i < 0 for pair in atoms.items() for i in pair
                )
                or any(old >= count for old in atoms)
                or set(atoms.values()) != set(range(len(atoms)))
            ):
                raise ValueError("Managed atom_index_map must enumerate retained atoms bijectively.")
            if len(set(atoms.values())) != len(atoms):
                raise ValueError("Managed atom_index_map must be injective.")
            atoms = {int(old): int(new) for old, new in atoms.items()}
        frames = plan.get("structure_index_map")
        frame_count = int(target.structures.n_structures)
        if frames is not None:
            frames = normalize_structure_index_map(frames, frame_count, len(frames))
        if (atoms is not None and not atoms) or (frames is not None and not frames):
            raise ValueError("Managed removal of every atom or structure is not received; use an independent output.")
        expected_atoms = len(atoms) if atoms is not None else count
        expected_frames = len(frames) if frames is not None else frame_count
        if axis_growth is not None:
            added = plan.get("added_count")
            if isinstance(added, bool) or not isinstance(added, Integral) or added < 0:
                raise ValueError("A prefix addition requires a nonnegative integer added_count.")
            if atoms is not None or frames is not None:
                raise ValueError("Prefix additions cannot also declare retained-axis maps.")
            if axis_growth == "atoms":
                atoms = dict(enumerate(range(count)))
                expected_atoms = count + int(added)
            else:
                frames = list(range(frame_count)) + [None] * int(added)
                expected_frames = frame_count + int(added)
        combined_atoms = (
            atoms
            if self._atoms is None
            else (
                self._atoms
                if atoms is None
                else {old: atoms[current] for old, current in self._atoms.items() if current in atoms}
            )
        )
        combined_frames = (
            frames
            if self._frames is None
            else (
                self._frames
                if frames is None
                else [None if index is None else self._frames[index] for index in frames]
            )
        )
        if combined_frames is not None:
            # Preflight structure-bound scene data before any destructive write.
            with self._internal():
                prepare_structure_edit(view, combined_frames)
        return (
            combined_atoms,
            combined_frames,
            expected_atoms,
            expected_frames,
        )

    @signal(tags=["edit"])
    @digest()
    def execute(self, callback, *, name, update_view=True, rejection_check=None, axis_growth=None, skip_digestion=False):
        """Execute one admitted native edit and optionally reconcile its scene.

        ``callback`` prepares a plan without mutating the target. The ``run``
        callable must execute science exactly once, returning the native result.
        A native atomic-failure declaration is trusted only while the target's
        state dictionary is still the very same object after an exception.
        An optional read-only ``rejection_check(target)`` returns an immutable
        family-owned token before execution and after rejection. It must also
        remain equal to certify nested-state preservation. An older host rejects
        this explicit keyword before science rather than ignoring a plan field.
        Other exceptions enter uncertain state and require explicit replacement.
        axis_growth is None, 'atoms' or 'structures'. A received provider may
        declare a prefix-preserving native addition plus plan['added_count'];
        new atoms/structures acquire no fabricated old scene/source identity.
        Preflight rejects unknown per-structure visual data before science.
        Retained maps and further additions compose across deferred edits.
        """
        if not isinstance(update_view, bool):
            raise TypeError("update_view must be a boolean.")
        if rejection_check is not None and not callable(rejection_check):
            raise TypeError("rejection_check must be a read-only token callable or None.")
        if axis_growth not in (None, "atoms", "structures"):
            raise ValueError("axis_growth must be None, 'atoms' or 'structures'.")
        with self._locked():
            view = self._view()
            if self._state not in {"synchronized", "pending"}:
                raise SystemEditPendingError(self._reason())
            target = view.molsys
            if target is None:
                raise ValueError("Load a molecular system before editing it.")
            if self._pending and target is not self._target:
                self._state, self._detail = "uncertain", "The pending target was replaced outside the coordinator."
                self._notify(view)
                raise SystemEditPendingError(self._detail)
            prior_state = self._state
            self._state = "editing"
            try:
                plan = callback(target)
                if (
                    not isinstance(plan, dict)
                    or not callable(plan.get("run"))
                    or not isinstance(plan.get("changed"), bool)
                ):
                    raise ValueError("An edit plan requires run and an explicit changed boolean.")
                policy = plan.get("interactions_policy", "invalidate")
                if policy not in {"preserve", "invalidate"}:
                    raise ValueError("Unsupported interaction validity policy.")
                atoms, frames, atom_count, frame_count = self._prepare_maps(view, target, plan, axis_growth)
                checkpoint = self._checkpoint or _SceneCheckpoint(view)
                before_rejection = None if rejection_check is None else rejection_check(target)
                if view.closed or view.molsys is not target:
                    raise RuntimeError("The view closed or its target changed during edit preparation.")
            except BaseException:
                self._state = prior_state
                raise
            self._operation_id = f"{name}:{uuid4()}"
            original_state = vars(target)
            self._target = target
            self._notify(view)
            try:
                result = plan["run"]()
            except BaseException:
                unchanged = vars(target) is original_state and (
                    plan.get("failure_atomic") is True or rejection_check is not None
                )
                if unchanged and rejection_check is not None:
                    try:
                        unchanged = (rejection_check(target) == before_rejection) is True
                    except Exception as exc:
                        from ._private.smonitor_emit import emit_suppressed_exception

                        unchanged = False
                        emit_suppressed_exception("SystemEditsManager.rejection_check", exc)
                if unchanged:
                    self._state = prior_state
                    if not self._pending:
                        self._target = None
                else:
                    self._checkpoint = checkpoint
                    self._state = "uncertain"
                    self._detail = (
                        "Science raised after a potentially partial write. Replace the system explicitly to recover."
                    )
                    self._quarantine(view)
                self._notify(view)
                raise
            if view.closed or view.molsys is not target:
                self._state, self._detail = "uncertain", "The view closed or its target changed during science."
                if not view.closed:
                    self._quarantine(view)
                    self._notify(view)
                raise SystemEditSyncError(self._operation_id, result)
            if int(target.get_n_atoms()) != atom_count or int(target.structures.n_structures) != frame_count:
                self._state, self._detail = (
                    "uncertain",
                    "The completed edit does not match its declared correspondence.",
                )
                self._checkpoint = checkpoint
                self._quarantine(view)
                self._notify(view)
                raise SystemEditSyncError(self._operation_id, result)
            if plan["changed"]:
                self._checkpoint = checkpoint
                self._atoms, self._frames = atoms, frames
                self._policy = "invalidate" if "invalidate" in {self._policy, policy} else "preserve"
                self._revision += 1
                self._pending += 1
                self._state, self._detail = "pending", None
                self._quarantine(view)
            else:
                self._state = prior_state
                if not self._pending:
                    self._target = None
            if update_view and self._pending:
                try:
                    self.synchronize(skip_digestion=True)
                except Exception as exc:
                    raise SystemEditSyncError(self._operation_id, result) from exc
            else:
                self._notify(view)
            return result

    def _quarantine(self, view):
        view._cancel_binary_structure_stream("managed molecular edit")
        # Do not let a stale lazy projection serialize the mutated live target.
        view._current_molecular_projection = None
        with self._internal():
            try:
                view.history.clear(skip_digestion=True)
            except Exception as exc:
                # clear() drops old-index snapshots before notifying the UI.
                # A disconnected connector must not hide scientific completion.
                from ._private.smonitor_emit import emit_suppressed_exception

                emit_suppressed_exception("SystemEditsManager.history_delivery", exc)

    @signal(tags=["edit"])
    @digest()
    def synchronize(self, *, skip_digestion=False):
        """Reconcile pending science without executing a scientific tool again."""
        with self._locked():
            view = self._view()
            if self._state == "synchronized":
                return
            if self._state not in {"pending", "sync_failed"} or view.molsys is not self._target:
                raise SystemEditPendingError(self._reason())
            self._state = "syncing"
            try:
                with self._internal():
                    self._checkpoint.restore(view)
                    view.apply_system_edit(
                        self._target,
                        atom_index_map=self._atoms,
                        structure_index_map=self._frames,
                        interactions_policy=self._policy,
                    )
            except Exception as exc:
                with self._internal():
                    self._checkpoint.restore(view)
                self._state, self._detail = "sync_failed", str(exc)
                self._quarantine(view)
                self._notify(view)
                raise
            self._integrated = self._revision
            self._reset()
            self._notify(view)

    def _reset(self):
        self._state, self._detail = "synchronized", None
        self._pending = 0
        self._target = self._checkpoint = self._atoms = self._frames = None
        self._policy = "preserve"

    @signal(tags=["edit"])
    @digest()
    def replace(self, molecular_system, *, skip_digestion=False):
        """Explicitly discard pending scene reconciliation and load a replacement.

        This does not undo a scientific edit or modify caller-held old systems.
        Cached addon facades resolve the newly loaded target on their next call.
        """
        with self._locked():
            view = self._view()
            if self._state in {"editing", "syncing"}:
                raise SystemEditPendingError("Cannot replace a system while an edit is executing.")
            try:
                with self._internal():
                    view.load(molecular_system, mode="replace")
            except Exception:
                self._state, self._detail = "uncertain", "Replacement failed; load a valid replacement explicitly."
                self._notify(view)
                raise
            self._revision += 1
            self._integrated = self._revision
            self._reset()
            self._notify(view)
