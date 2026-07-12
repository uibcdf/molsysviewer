from __future__ import annotations


from typing import Any
import numpy as np
import molsysmt as msm

from smonitor import signal
from .._pyunitwizard import puw
from .._private.arg_digestion import digest
from ..regions import Region
from ..figures import FigureSpec
from ..whole import Whole
from .signals import (
    zoom_signal_extra as _zoom_signal_extra,
    camera_snapshot_extra as _camera_snapshot_extra,
)

_NM_TO_ANGSTROM = puw.conversion_factor("nm", "angstroms")


class SceneMixin:
    _BOX_TAG = "__msv_box"

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
        sidx = 0 if structure_indices in ("all", None) else int(structure_indices)

        box_q = msm.get(self._molsys, element="system", box=True, skip_digestion=True)
        if box_q is None:
            raise ValueError("The loaded system does not have box information.")

        box_nm = puw.get_value(box_q)  # shape (n_structures, 3, 3) in nm
        if box_nm.ndim == 3:
            box_nm = box_nm[sidx]  # shape (3, 3)

        # Convert nm → Å
        box_a = box_nm * _NM_TO_ANGSTROM  # (3, 3) in Å
        a, b, c = box_a[0], box_a[1], box_a[2]

        # Build 8 vertices
        O = np.array([0.0, 0.0, 0.0])
        v000 = O
        v100 = O + a
        v010 = O + b
        v001 = O + c
        v110 = O + a + b
        v101 = O + a + c
        v011 = O + b + c
        v111 = O + a + b + c

        # 12 box edges
        edges = [
            # along a
            [v000.tolist(), v100.tolist()], [v010.tolist(), v110.tolist()],
            [v001.tolist(), v101.tolist()], [v011.tolist(), v111.tolist()],
            # along b
            [v000.tolist(), v010.tolist()], [v100.tolist(), v110.tolist()],
            [v001.tolist(), v011.tolist()], [v101.tolist(), v111.tolist()],
            # along c
            [v000.tolist(), v001.tolist()], [v100.tolist(), v101.tolist()],
            [v010.tolist(), v011.tolist()], [v110.tolist(), v111.tolist()],
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
        duration: Any = '250 ms',
        duration_ms: Any | None = None,
        extra_radius: Any = '4.0 angstroms',
        min_radius: Any = '1.0 angstroms',
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
        duration: Any = '250 ms',
        duration_ms: Any | None = None,
        extra_radius: Any = '4.0 angstroms',
        min_radius: Any = '1.0 angstroms',
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
        duration: Any = '250 ms',
        duration_ms: Any | None = None,
        extra_radius: Any = '4.0 angstroms',
        min_radius: Any = '1.0 angstroms',
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
            annotation_tags = [
                tag for tag, layer in self._scene_objects.items() if getattr(layer, "kind", None) == "annotation"
            ]
            for tag in annotation_tags:
                self._scene_objects.pop(tag, None)
                self._layers.pop(tag, None)
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
        atom_indices = msm.select(
            self._molsys,
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
        )
        self._molsys.structures.set_coordinates(
            indices=atom_indices,
            structure_indices=structure_indices,
            value=coordinates,
            skip_digestion=True,
        )
        visible = self.visible_atom_indices
        self.apply_system_edit(self._molsys, visible_atom_indices=visible)

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
        """Dynamically update coordinates in-place in both Python and the frontend WebGL buffers.

        This avoids expensive representation rebuilds.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded.")

        atom_indices = msm.select(
            self._molsys,
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
        )
        if len(atom_indices) == 0:
            return

        from .._pyunitwizard import puw
        if puw.is_quantity(coordinates):
            coords_nm = puw.get_value(coordinates, to_unit="nm")
        else:
            coords_nm = coordinates

        self._molsys.structures.set_coordinates(
            indices=atom_indices,
            structure_indices=structure_indices,
            value=coordinates,
            skip_digestion=True,
        )

        coords_arr = np.atleast_2d(coords_nm)
        if coords_arr.ndim == 3:
            coords_arr = coords_arr[0]
        coords_ang = (coords_arr * _NM_TO_ANGSTROM).tolist()

        self._send({
            "op": "partial_coordinates_update",
            "coordinates": coords_ang,
            "atom_indices": list(atom_indices),
            "transaction_id": transaction_id,
        })

    @signal(tags=["viewer"])
    @digest()
    def reset_viewer(self, skip_digestion: bool = False) -> None:
        """Fully clear the viewer and reset internal state (requires a new `load(...)`)."""
        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None
        self.structure_mask = None
        self._regions.clear()
        self._layers.clear()
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
            }
        )

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
