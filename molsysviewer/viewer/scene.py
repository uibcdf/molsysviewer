from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np
from smonitor import signal

from .._private.argdigest import digest
from .._pyunitwizard import puw
from ..figures import FigureSpec
from ..regions import Region
from ..whole import Whole
from .signals import (
    camera_snapshot_extra as _camera_snapshot_extra,
)
from .signals import (
    zoom_signal_extra as _zoom_signal_extra,
)

_NM_TO_ANGSTROM = puw.conversion_factor("nm", "angstroms")


class SceneMixin:
    _BOX_TAG = "__msv_box"

    @signal(tags=["scene", "box", "edit"])
    @digest()
    def set_box(
        self,
        box=None,
        *,
        molecular_system=None,
        structure_indices: Any = "all",
        source_structure_indices: Any = "all",
        structure_pairing: str | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Assign the whole-system cell without moving coordinates.

        ``box`` requires length units and three row vectors, with shape (3, 3)
        or (selected structures, 3, 3). One submitted matrix applies uniformly
        to the selected structures. ``None`` removes the complete cell series.
        Initialization and removal require all destination structures; partial
        replacement requires an existing series.

        Alternatively, ``molecular_system`` declares a supported MolSysMT source
        from which to read the cell. Selected source/destination counts must
        agree, with ``structure_pairing='by_index'`` for more than one structure.
        Their times must agree when both are present. Sources never broadcast.

        This edit invalidates interactions only on affected structures, clears
        scene undo/redo, retains source correspondence and refreshes the canvas.
        Scientific data and input preparation are checked before mutation;
        arbitrary runtime/render failures do not have a rollback guarantee.
        """
        from .._private.argdigest.argument.box import _box_values
        from .._private.argdigest.argument.molecular_system import _normalize_paths
        from ..interactions import _indices

        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        if structure_pairing not in (None, "by_index"):
            raise ValueError("structure_pairing must be None or 'by_index'.")
        count = int(self._molsys.structures.n_structures)

        def selected(value, total, name):
            if value is None or isinstance(value, str) and value == "all":
                return list(range(total))
            result = _indices(value, total, name, unique=False).tolist()
            if not result or len(set(result)) != len(result):
                raise ValueError(f"{name} must contain nonempty, unique structure indices.")
            return result

        frames = selected(structure_indices, count, "structure_indices")
        complete = len(frames) == count
        source = molecular_system is not None
        if source:
            if box is not None:
                raise ValueError("Provide either box or molecular_system, not both.")
            molecular_system = _normalize_paths(molecular_system)
            source_count = int(msm.get(molecular_system, n_structures=True))
            source_frames = selected(source_structure_indices, source_count, "source_structure_indices")
            if len(source_frames) != len(frames):
                raise ValueError(
                    "Selected source and destination structure counts must agree; sources do not broadcast."
                )
            if len(frames) > 1 and structure_pairing != "by_index":
                raise ValueError("Reading multiple source cells requires structure_pairing='by_index'.")
            box = msm.get(molecular_system, structure_indices=source_frames, box=True)
            if box is None:
                raise ValueError("The declared source has no box information.")
            source_time = msm.get(molecular_system, structure_indices=source_frames, time=True)
            target_time = self._molsys.structures.time
            if source_time is not None and target_time is not None:
                if not np.allclose(
                    puw.get_value(source_time, to_unit="ps"),
                    puw.get_value(target_time, to_unit="ps")[frames],
                    rtol=1e-9,
                    atol=1e-9,
                ):
                    raise ValueError("Selected source times do not match the destination time axis.")
        elif (
            not (
                source_structure_indices is None
                or isinstance(source_structure_indices, str)
                and source_structure_indices == "all"
            )
            or structure_pairing is not None
        ):
            raise ValueError("Source selectors and pairing require molecular_system.")

        existing = self._molsys.structures.box
        if box is None:
            if not complete:
                raise ValueError("Box removal requires all destination structures.")
            if existing is None:
                return
            quantity = None
        else:
            values = _box_values(box)
            if len(values) != len(frames) and (source or len(values) != 1):
                raise ValueError("Box count must match the selected destination structures.")
            if existing is None and not complete:
                raise ValueError("Initialize every structure's box before replacing a subset.")
            updated = (
                np.empty((count, 3, 3), dtype=float)
                if existing is None
                else np.array(
                    puw.get_value(existing, to_unit="nm"),
                    dtype=float,
                    copy=True,
                )
            )
            updated[frames] = values
            quantity = puw.quantity(updated, "nm")

        analyses = getattr(self._molsys, "interactions", {})
        reconciled = {name: result.invalidate_structures(frames) for name, result in analyses.items()}
        previous_box = (
            None
            if existing is None
            else puw.quantity(
                np.array(puw.get_value(existing, to_unit="nm"), copy=True),
                "nm",
            )
        )
        msm.set(self._molsys, box=quantity)
        # Older compatible base providers can silently ignore cell initialization.
        # Verify through the same public scientific route used by projections.
        actual = msm.get(self._molsys, box=True)
        applied = (
            actual is None
            if quantity is None
            else (
                actual is not None
                and np.shape(puw.get_value(actual, to_unit="nm")) == np.shape(updated)
                and np.allclose(puw.get_value(actual, to_unit="nm"), updated, rtol=1e-12, atol=1e-12)
            )
        )
        if not applied:
            msm.set(self._molsys, box=previous_box)
            raise ValueError("MolSysMT did not apply the requested box. This edit requires a compatible provider.")
        if analyses:
            self._molsys.interactions = reconciled
        self.apply_system_edit(self._molsys, interactions_policy="preserve", skip_digestion=True)

    def _refresh_box_display(self):
        """Regenerate visible box edges from the current scientific cell."""
        if self._box_record is None:
            return
        if self._molsys.structures.box is None:
            self.hide_box(skip_digestion=True)
            return
        style = self._box_record
        self.show_box(
            color=style["color"],
            width=style["width"],
            alpha=style["alpha"],
            structure_indices=self.player.index,
            skip_digestion=True,
        )

    @signal(tags=["scene", "box"])
    @digest()
    def show_box(
        self,
        color: Any = "grey",
        width: float = 0.15,
        alpha: float = 1.0,
        structure_indices: Any = 0,
        skip_digestion: bool = False,
    ) -> None:
        """Render the unit-cell or simulation-box edges in the canvas."""
        # The digester turns an int into np.array([i]); int() on a 1-d array is an error
        # under NumPy 2, which broke show_box() even with its default arguments.
        if structure_indices is None or isinstance(structure_indices, str):
            sidx = 0
        else:
            sidx = int(np.asarray(structure_indices).reshape(-1)[0])

        box_q = msm.get(self._molsys, element="system", box=True, skip_digestion=True)
        if box_q is None:
            raise ValueError("The loaded system does not have box information.")

        # The frontend draws in Å. MolSysMT returns the box in the session's standard
        # length, which the user may have set to anything; convert explicitly
        # (uibcdf/molsysviewer#96).
        box_a = np.asarray(puw.get_value(box_q, to_unit="angstrom"))  # (n_structures, 3, 3)
        if box_a.ndim == 3:
            box_a = box_a[sidx]  # shape (3, 3)
        a, b, c = box_a[0], box_a[1], box_a[2]

        # Build 8 vertices
        origin = np.array([0.0, 0.0, 0.0])
        v000 = origin
        v100 = origin + a
        v010 = origin + b
        v001 = origin + c
        v110 = origin + a + b
        v101 = origin + a + c
        v011 = origin + b + c
        v111 = origin + a + b + c

        # 12 box edges
        edges = [
            # along a
            [v000.tolist(), v100.tolist()],
            [v010.tolist(), v110.tolist()],
            [v001.tolist(), v101.tolist()],
            [v011.tolist(), v111.tolist()],
            # along b
            [v000.tolist(), v010.tolist()],
            [v100.tolist(), v110.tolist()],
            [v001.tolist(), v011.tolist()],
            [v101.tolist(), v111.tolist()],
            # along c
            [v000.tolist(), v001.tolist()],
            [v100.tolist(), v101.tolist()],
            [v010.tolist(), v011.tolist()],
            [v110.tolist(), v111.tolist()],
        ]

        from ..colors import normalize_color as _nc

        color_int = _nc(color)

        if self._box_visible:
            self._send({"op": "clear_shapes_by_tag", "tag": self._BOX_TAG})

        msg = {
            "op": "add_network_links",
            "options": {
                "mode": "coordinates",
                "coordinate_pairs": edges,
                "radii": float(width),
                "colors": color_int,
                "alpha": float(alpha),
                "tag": self._BOX_TAG,
            },
        }
        self._send(msg)
        self._box_visible = True
        self._box_record = {
            "color": color,
            "width": float(width),
            "alpha": float(alpha),
            "structure_indices": sidx,
        }

    @signal(tags=["scene", "box"])
    @digest()
    def hide_box(self, skip_digestion: bool = False) -> None:
        """Remove the box edge display from the canvas."""
        if not self._box_visible:
            return
        self._send({"op": "clear_shapes_by_tag", "tag": self._BOX_TAG})
        self._box_visible = False
        self._box_record = None

    @signal(tags=["camera"], extra_factory=_zoom_signal_extra)
    @digest()
    def zoom(
        self,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on a selection. Delegate to ``view.camera.zoom()``."""
        self.camera.zoom(
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["camera", "selection"], extra_factory=_zoom_signal_extra)
    @digest()
    def focus_selection(
        self,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on a selection. Delegate to ``view.camera.focus_selection()``."""
        self.camera.focus_selection(
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["camera", "region"])
    @digest()
    def focus_region(
        self,
        region: str | Region,
        *,
        duration: Any = "250 ms",
        duration_ms: Any | None = None,
        extra_radius: Any = "4.0 angstroms",
        min_radius: Any = "1.0 angstroms",
        skip_digestion: bool = False,
    ) -> None:
        """Focus the camera on a region. Delegate to ``view.camera.focus_region()``."""
        self.camera.focus_region(
            region=region,
            duration=duration,
            duration_ms=duration_ms,
            extra_radius=extra_radius,
            min_radius=min_radius,
            skip_digestion=True,
        )

    @signal(tags=["scene"])
    @digest()
    def clear_decorations(
        self,
        *,
        shapes: bool = True,
        styles: bool = True,
        labels: bool = True,
        skip_digestion: bool = False,
    ) -> None:
        """Clear decorative elements (shapes/styles/labels) without touching the loaded structure or camera."""
        if shapes:
            self._shape_history.clear()
        if labels:
            self._annotation_history.clear()
            annotation_tags = [tag for (kind, tag) in self._scene_objects if kind == "annotation"]
            for tag in annotation_tags:
                self._scene_objects.pop(("annotation", tag), None)
                dict.pop(self._layers, tag, None)
        self._send(
            {
                "op": "clear_scene",
                "options": {
                    "shapes": bool(shapes),
                    "styles": bool(styles),
                    "labels": bool(labels),
                },
            }
        )

    @signal(tags=["camera"])
    @digest()
    def reset_camera(self, skip_digestion: bool = False) -> None:
        """Reset the camera. Delegate to ``view.camera.reset()``."""
        self.camera.reset(skip_digestion=True)

    @property
    def current_structure_id(self):
        """ID of the structure currently displayed (requires a loaded molecular system)."""
        if self._molsys is None:
            return None
        try:
            ids = msm.get(
                self._molsys,
                element="structure",
                structure_indices=[self._current_structure_index],
                structure_id=True,
                skip_digestion=True,
            )
            if ids is not None:
                try:
                    return ids[0]
                except (IndexError, TypeError):
                    return ids
        except Exception:
            pass
        return None

    @signal(tags=["structures"])
    @digest()
    def set_structure(self, index: int, skip_digestion: bool = False) -> None:
        """Jump to a specific structure (frame) index."""
        self.player.go_to_structure(int(index), skip_digestion=True)

    @signal(tags=["structures"])
    @digest()
    def play(
        self,
        fps: int | None = None,
        mode: str | None = None,
        direction: str | None = None,
        step: int | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Start playback through structures."""
        self.player.play(
            fps=fps,
            mode=mode,
            direction=direction,
            step_size=step,
            skip_digestion=True,
        )

    @signal(tags=["structures"])
    @digest()
    def pause(self, skip_digestion: bool = False) -> None:
        """Pause playback."""
        self.player.pause(skip_digestion=True)

    @signal(tags=["structures"])
    @digest()
    def set_play_speed(self, fps: int, skip_digestion: bool = False) -> None:
        """Update the playback frame rate."""
        self.player.set_fps(int(fps), skip_digestion=True)

    @signal(tags=["query"])
    @digest()
    def get_coordinates(
        self,
        selection: Any = "all",
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
    ):
        """Return atom coordinates from the loaded molecular system."""
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        atom_indices = msm.select(
            self._molsys,
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
        )
        return self._molsys.structures.get_coordinates(
            indices=atom_indices,
            structure_indices=structure_indices,
            skip_digestion=True,
        )

    @signal(tags=["viewer"])
    @digest()
    def set_coordinates(
        self,
        coordinates,
        selection: Any = "all",
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
    ) -> None:
        """Replace atom coordinates in the loaded molecular system and update the canvas."""
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")
        atoms, structures, _ = self._edit_coordinates(coordinates, selection, structure_indices, syntax)
        if atoms and structures:
            self.apply_system_edit(self._molsys, interactions_policy="preserve", skip_digestion=True)

    def _edit_coordinates(self, coordinates, selection, structure_indices, syntax):
        """Validate before writing and reconcile derived scientific state."""
        from .._pyunitwizard import puw
        from ..interactions import _indices

        atoms = list(msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True))
        count = int(self._molsys.structures.n_structures)
        if structure_indices is None or isinstance(structure_indices, str) and structure_indices == "all":
            structures = list(range(count))
        else:
            structures = _indices(structure_indices, count, "structure_indices", unique=False).tolist()
        if len(set(structures)) != len(structures):
            raise ValueError("Coordinate edits require unique structure indices.")
        if not atoms or not structures:
            return atoms, structures, []
        if not puw.is_quantity(coordinates):
            raise ValueError("Coordinates require an explicit length unit.")
        values = np.asarray(puw.get_value(coordinates, to_unit="nm"), dtype=float)
        if values.ndim == 1:
            values = values[None, None, :]
        elif values.ndim == 2:
            values = values[None, :, :]
        if values.ndim != 3 or values.shape[1:] != (len(atoms), 3):
            raise ValueError("Coordinates must have shape (structures, selected atoms, 3).")
        if values.shape[0] not in {1, len(structures)} or not np.isfinite(values).all():
            raise ValueError("Coordinates must be finite and match the selected structures.")
        values = np.broadcast_to(values, (len(structures), len(atoms), 3)).copy()
        analyses = getattr(self._molsys, "interactions", {})
        reconciled = {name: result.invalidate_structures(structures) for name, result in analyses.items()}
        self._molsys.structures.set_coordinates(
            indices=atoms,
            structure_indices=structures,
            value=puw.quantity(values, "nm"),
            skip_digestion=True,
        )
        if analyses:
            self._molsys.interactions = reconciled
        self.interactions._system_changed()
        self._source_binding_memo = None
        self.history.clear()
        self._clear_dynamic_region_cache()
        self._current_molecular_projection = self._new_lazy_molecular_projection(label=self._last_label)
        return atoms, structures, (values * _NM_TO_ANGSTROM).tolist()

    @signal(tags=["viewer"])
    @digest()
    def partial_coordinates_update(
        self,
        coordinates,
        selection: Any = "all",
        structure_indices: Any = 0,
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
        transaction_id: str | int | None = None,
    ) -> None:
        """Edit selected structures and reconcile their model and derived state.

        Only edited coordinate arrays are copied in the browser. Mol* updates
        dependent representations from the revised trajectory models.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")

        pending_transfer = any(manager.active is not None for _, manager in self._iter_structure_transfer_managers())
        atom_indices, structures, coordinates_a = self._edit_coordinates(
            coordinates,
            selection,
            structure_indices,
            syntax,
        )
        if not atom_indices or not structures:
            return
        if pending_transfer:
            # Supersede old native buffers and their lazy fallback before
            # sending edits; transport defers the edit behind the new model.
            self.apply_system_edit(self._molsys, interactions_policy="preserve", skip_digestion=True)

        self._send(
            {
                "op": "partial_coordinates_update",
                "coordinates": coordinates_a,
                "coordinate_unit": "angstrom",
                "atom_indices": list(atom_indices),
                "structure_indices": structures,
                "transaction_id": transaction_id,
            }
        )
        changed = self._evaluate_dynamic_regions_for_frame(self.player.index)
        if changed:
            self._send_runtime_only({"op": "set_dynamic_region_atoms", "frame": self.player.index, "regions": changed})
        self._sync_measurement_summaries_runtime()
        self.interactions._project()

    @signal(tags=["viewer"])
    @digest()
    def reset_viewer(self, skip_digestion: bool = False) -> None:
        """Fully clear the viewer and reset internal state (requires a new `load(...)`)."""
        self._reset_viewer()

    def _reset_viewer(self, *, awaiting_structure: bool = False) -> None:
        """Clear the session, optionally as the first step of a prepared load."""
        self._cancel_binary_structure_stream("viewer reset")
        self._molecular_projection_revision += 1
        self._current_molecular_projection = None
        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.structure_mask = None
        for obj in [
            *self._regions.values(),
            *self._layers.values(),
            *self._scene_objects.values(),
            *self._selections.values(),
        ]:
            obj._active = False
        dict.clear(self._regions)
        dict.clear(self._layers)
        self._scene_objects.clear()
        self._selections.clear()
        for manager in self._tag_managers.values():
            manager.reset()
        self._region_order_counter = 0
        self._global_hidden = False
        self._box_visible = False
        self._box_record = None
        self._atom_color_layers = {"whole": {}}
        self._atom_color_map = {}
        self.whole = Whole(self)
        self._shape_history.clear()
        self._annotation_history.clear()
        self._measurement_history.clear()
        self._section_history.clear()
        self._selection_history.clear()
        self._last_active_selection_event = None
        self._active_selection_recipe.clear()
        self._scene_look.clear()
        self._clear_dynamic_region_cache()
        self._player_state.clear()
        self.player._reset_state()  # noqa: SLF001
        self._last_label = None
        self._current_figure_spec = None
        self._current_structure_index = 0
        self._reset_load_blocks()

        self._send(
            {
                "op": "clear_all",
                "options": {},
                "awaiting_structure": awaiting_structure,
            }
        )
        self._sync_trajectory_summary_runtime()

    @signal(tags=["camera"], extra_factory=_camera_snapshot_extra)
    @digest()
    def get_camera_snapshot(self, *, pretty: bool = False, skip_digestion: bool = False) -> dict | str | None:
        """Return the last camera snapshot. Delegate to ``view.camera.get_snapshot()``."""
        return self.camera.get_snapshot(pretty=pretty, skip_digestion=True)

    @signal(tags=["camera"], extra_factory=_camera_snapshot_extra)
    @digest()
    def set_camera_snapshot(self, snapshot: dict, *, duration_ms: int = 0, skip_digestion: bool = False) -> None:
        """Apply a camera snapshot. Delegate to ``view.camera.set_snapshot()``."""
        self.camera.set_snapshot(snapshot, duration_ms=duration_ms, skip_digestion=True)

    @signal(tags=["figure"])
    @digest()
    def set_figure_spec(self, figure_spec: FigureSpec, *, skip_digestion: bool = False) -> None:
        """Anchor a figure recipe to the viewer workbench Scene section."""
        if not isinstance(figure_spec, FigureSpec):
            raise TypeError("set_figure_spec expects a FigureSpec instance.")
        payload: dict = {
            "op": "set_figure_spec",
            "figure_preset": figure_spec.preset,
            "figure_scale": float(figure_spec.scale),
            "figure_variants": list(figure_spec.build_publication_variants().keys()),
        }
        self._current_figure_spec = dict(payload)
        self._send(payload)


SceneMixin.__module__ = "molsysviewer.viewer"
for _name, _value in SceneMixin.__dict__.items():
    if callable(_value):
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass
