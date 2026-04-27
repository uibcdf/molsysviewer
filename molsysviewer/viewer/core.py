from __future__ import annotations

from typing import Any, Dict, Mapping
import base64
import json
import time
import inspect
import re

import molsysmt as msm
import numpy as np
from smonitor import signal
from smonitor.integrations import emit_from_catalog
from depdigest import dep_digest

from .._pyunitwizard import puw
from .._private.arg_digestion import digest
from .._private.smonitor import CATALOG, PACKAGE_ROOT, META
from .._private.variables import is_all
from ..widget import MolSysViewerWidget
from ..loaders import load_from_molsysmt as _load_from_molsysmt
from ..annotations import AnnotationsManager
from ..active_selection import ActiveSelection
from ..addons import AddonPanelWidget, ViewAddonsManager, addons as global_addons
from ..exports import ExportManager
from ..figures import FigureSpec
from ..interaction_targets import InteractionTarget
from ..measurements import MeasurementsManager
from ..player import PlayerManager
from ..scene import SceneManager
from ..selections import SelectionsManager, Selection
from ..styles import StylesManager
from ..shapes import ShapesManager
from ..regions import Region
from ..whole import Whole
from ..layers import Layer, SceneObject
from ..colors import colors as global_colors
from .. import config
from .history import HistoryMixin
from .camera import CameraManager
from .movie import MovieManager
from .export import ExportMixin
from .scene_registry import SceneRegistryMixin
from .representations import normalize_representation_type
from .presets import normalize_representation_preset, resolve_user_preset
from .signals import (
    camera_snapshot_extra as _camera_snapshot_extra,
    controls_signal_extra as _controls_signal_extra,
    load_signal_extra as _load_signal_extra,
    panel_mode_signal_extra as _panel_mode_signal_extra,
    panel_mode_state_query_extra as _panel_mode_state_query_extra,
    resolve_entry_callable as _resolve_entry_callable,
    workspace_catalog_signal_extra as _workspace_catalog_signal_extra,
    workspace_panel_signal_extra as _workspace_panel_signal_extra,
    workspace_panels_signal_extra as _workspace_panels_signal_extra,
    workspace_runtime_signal_extra as _workspace_runtime_signal_extra,
    workspace_sections_signal_extra as _workspace_sections_signal_extra,
    workspace_signal_extra as _workspace_signal_extra,
    zoom_signal_extra as _zoom_signal_extra,
)

_HTML_MANAGER_VERSION = "1.0.1"
_WIDGETS_BASE_VERSION = "2.0.0"


class ViewerInfo:
    """Wrapper for the dual-section output of ``MolSysView.info(source='all')``.

    Holds the *molsys* and *view* sections (pandas Stylers by default) and
    renders both sequentially in Jupyter via ``_repr_html_()``.
    """

    def __init__(self, molsys_section: Any, view_section: Any) -> None:
        self.molsys = molsys_section
        self.view = view_section

    def _repr_html_(self) -> str:
        parts: list[str] = []
        for label, section in (("Molecular system", self.molsys), ("Viewer", self.view)):
            parts.append(f"<h4 style='margin:0.6em 0 0.2em'>{label}</h4>")
            html_method = getattr(section, "_repr_html_", None)
            if html_method is not None:
                parts.append(html_method())
            else:
                parts.append(f"<pre>{section!r}</pre>")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"ViewerInfo(molsys={self.molsys!r}, view={self.view!r})"

    def __getitem__(self, key: str) -> Any:
        if key == "molsys":
            return self.molsys
        if key == "view":
            return self.view
        raise KeyError(key)

    def keys(self):
        return ("molsys", "view")


class RegionInfo:
    """Wrapper for the dual-section output of ``Region.info()``.

    Holds a *molsys* section (filtered to the region's atoms) and a *region*
    section (tag, atom count, visibility, representation) and renders both
    sequentially in Jupyter via ``_repr_html_()``.
    """

    def __init__(self, tag: str, molsys_section: Any, region_section: Any) -> None:
        self.tag = tag
        self.molsys = molsys_section
        self.region = region_section

    def _repr_html_(self) -> str:
        parts: list[str] = [f"<h4 style='margin:0.6em 0 0.2em'>Region: {self.tag}</h4>"]
        for label, section in (("Molecular system", self.molsys), ("Region state", self.region)):
            parts.append(f"<h5 style='margin:0.4em 0 0.15em;color:#555'>{label}</h5>")
            html_method = getattr(section, "_repr_html_", None)
            if html_method is not None:
                parts.append(html_method())
            else:
                parts.append(f"<pre>{section!r}</pre>")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"RegionInfo(tag={self.tag!r}, molsys={self.molsys!r}, region={self.region!r})"

    def __getitem__(self, key: str) -> Any:
        if key == "molsys":
            return self.molsys
        if key == "region":
            return self.region
        raise KeyError(key)

    def keys(self):
        return ("molsys", "region")


from .utils import quantity_value_in_unit as _quantity_value_in_unit


class MolSysView(SceneRegistryMixin, HistoryMixin, ExportMixin):
    """Mol* viewer widget with a Python-facing API.

    Provides structure loading, visibility control, shape management, and
    utilities to export static HTML views for documentation or sharing.
    """
    def _repr_mimebundle_(self, include=None, exclude=None):
        """IPython/Jupyter display hook (delegates to the underlying widget)."""
        return self.widget._repr_mimebundle_(include=include, exclude=exclude)

    @signal(tags=["viewer", "init"])
    @dep_digest('anywidget')
    @dep_digest('molsysmt')
    def __init__(self, *, debug_js: bool | None = None) -> None:
        self.widget = MolSysViewerWidget()
        self._debug_js = bool(debug_js) if debug_js is not None else False
        self.widget.debug_js = self._debug_js
        self._js_logs: list[dict[str, str]] = []
        try:
            self.widget.show_controls = bool(config.show_controls)
        except Exception:
            # If config is missing or misconfigured, fall back to defaults.
            self.widget.show_controls = True

        self.widget.layout.width = "100%"
        self.widget.layout.height = "480px"  # adjust if you prefer a taller default
        self.widget.layout.min_height = "400px"

        self._already_shown = False

        self._ready = False
        self._pending_messages: list[dict] = []
        self._message_history: list[dict] = []
        self._last_camera_snapshot: dict | None = None
        self._current_figure_spec: dict | None = None
        self._last_image_export_event: dict | None = None
        self._movie_export_frames: list | None = None
        self._movie_export_done: bool = False
        self._last_hover_event: dict | None = None
        self._last_click_event: dict | None = None
        self._last_context_event: dict | None = None
        self._last_context_action_event: dict | None = None
        self._hover_callbacks: list = []
        self._click_callbacks: list = []
        self._context_callbacks: list = []
        self._last_active_selection_event: dict | None = None
        self._last_tool_state_event: dict | None = None
        self._last_measurement_created_event: dict | None = None
        self._last_panel_mode_state_event: dict | None = None
        self._shape_history: list[dict] = []
        self._annotation_history: list[dict] = []
        self._measurement_history: list[dict] = []
        self._section_history: list[dict] = []
        self._selection_history: list[dict] = []
        self._last_label: str | None = None
        self._empty = True
        self._load_blocks: list[dict[str, Any]] = []
        self._current_structure_index: int = 0

        self._regions: Dict[str, Region] = {}
        self._layers: Dict[str, Layer] = {}
        self._scene_objects: Dict[str, SceneObject] = {}
        self._selections: Dict[str, Selection] = {}
        self._region_counter = 0
        self._annotation_counter = 0
        self._layer_counter = 0
        self._measurement_counter = 0
        self._shape_counter = 0
        self._section_counter = 0
        self._global_hidden = False
        self._box_visible = False
        self._box_record: dict | None = None  # params last passed to show_box
        self._atom_color_map: dict[int, int] = {}  # atomIndex → 0xRRGGBB
        self._active_panel_widget: tuple[str, str, AddonPanelWidget] | None = None

        self.whole = Whole(self)
        self.styles = StylesManager(self)
        self.colors = global_colors
        self.addons = ViewAddonsManager(self, global_addons)
        self.addons.bind_runtime()
        self.export = ExportManager(self)
        self.hover_target = InteractionTarget(
            self,
            event_getter_name="get_last_hover_event",
            empty_event_name="interaction_hover",
        )
        self.context_target = InteractionTarget(
            self,
            event_getter_name="get_last_context_event",
            empty_event_name="interaction_context_menu",
        )

        # Register callback for JS->Python messages
        def _handle_msg(widget, content, buffers):  # type: ignore[override]
            self._handle_frontend_event(content)

        self.widget.on_msg(_handle_msg)

        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None
        self.structure_mask = None

        self.shapes = ShapesManager(self)
        self.annotations = AnnotationsManager(self)
        self.active_selection = ActiveSelection(self)
        self.measurements = MeasurementsManager(self)
        self.selections = SelectionsManager(self)
        self.scene = SceneManager(self)
        self.player = PlayerManager(self)
        self.camera = CameraManager(self)
        self.movie = MovieManager(self)
        try:
            self.widget.autohide_controls = bool(config.autohide_controls)
        except Exception:
            self.widget.autohide_controls = False

        try:
            pos = list(config.controls_position)
            self.widget.controls_position = pos
        except Exception:
            self.widget.controls_position = ["top", "right"]

        try:
            pos_fs = list(config.controls_position_fullscreen)
            self.widget.controls_position_fullscreen = pos_fs
        except Exception:
            self.widget.controls_position_fullscreen = ["bottom", "right"]

        try:
            mode = str(config.controls_mode)
            self.widget.controls_mode = mode if mode in ("classic", "minimal") else "classic"
        except Exception:
            self.widget.controls_mode = "classic"

        try:
            style = str(config.panel_mode_style)
            self.widget.panel_mode_style = style if style in ("drawer", "floating") else "drawer"
        except Exception:
            self.widget.panel_mode_style = "drawer"

    def _handle_frontend_event(self, content: Mapping[str, Any]) -> None:
        event = content.get("event")
        if event == "ready":
            self._ready = True
            for msg in self._pending_messages:
                self.widget.send(msg)
            self._pending_messages.clear()
        elif event == "region_ack":
            tag = content.get("tag")
            if tag and tag in self._regions:
                region = self._regions[tag]
                region.atom_indices = content.get("atom_indices") or region.atom_indices
                if content.get("selection") is not None:
                    region.selection = content.get("selection")
        elif event == "region_deleted":
            tag = content.get("tag")
            if tag:
                self._unregister_region(tag)
        elif event == "layer_ack":
            tag = content.get("tag")
            # Ignore acks for tags that are already registered as individual scene
            # objects (shapes/annotations/measurements).  Mol* sends a layer_ack
            # for every Mol* node — including one per sphere in a batch — but
            # Python tracks those under _scene_objects, not _layers.
            if tag and tag not in self._scene_objects:
                if tag not in self._layers:
                    layer = Layer(self, tag, kind=content.get("kind"), meta=content.get("meta") or {})
                    self._layers[tag] = layer
                else:
                    layer = self._layers[tag]
                    layer.kind = content.get("kind", layer.kind)
                    if content.get("meta"):
                        layer.meta.update(content.get("meta"))
        elif event == "layer_deleted":
            tag = content.get("tag")
            if tag:
                self._unregister_layer(tag)
        elif event == "registry_cleared":
            pass  # frontend acknowledged clear_all; Python state is managed explicitly
        elif event == "js_log" and self._debug_js:
            level = str(content.get("level", "info")).upper()
            message = content.get("message", "")
            entry = {"level": level, "message": message}
            self._js_logs.append(entry)
            print(f"[JS {level}] {message}")
        elif event == "camera_snapshot":
            snapshot = content.get("snapshot")
            if isinstance(snapshot, dict):
                self._last_camera_snapshot = snapshot
        elif event == "image_export":
            self._last_image_export_event = dict(content)
        elif event == "movie_frame":
            if self._movie_export_frames is not None:
                self._movie_export_frames.append(dict(content))
        elif event == "movie_export_done":
            self._movie_export_done = True
        elif event == "interaction_hover":
            self._last_hover_event = dict(content)
            for cb in list(self._hover_callbacks):
                cb(self._last_hover_event)
        elif event == "interaction_click":
            self._last_click_event = dict(content)
            for cb in list(self._click_callbacks):
                cb(self._last_click_event)
        elif event == "interaction_context_menu":
            self._last_context_event = dict(content)
            for cb in list(self._context_callbacks):
                cb(self._last_context_event)
        elif event == "interaction_context_action":
            self._last_context_action_event = dict(content)
            action = content.get("action")
            if action == "addon_context_action":
                addon = content.get("addon")
                addon_action_id = content.get("addon_action_id")
                if not isinstance(addon, str) or addon.strip() == "":
                    raise ValueError("addon_context_action requires non-empty addon.")
                if not isinstance(addon_action_id, str) or addon_action_id.strip() == "":
                    raise ValueError("addon_context_action requires non-empty addon_action_id.")
                self.addons.handle_context_action(
                    addon.strip(),
                    addon_action_id.strip(),
                    dict(content),
                    skip_digestion=True,
                )
                self._sync_addons_runtime()
                return
            if action == "create_region_from_selection":
                raw_tag = content.get("tag")
                region_tag = raw_tag.strip() if isinstance(raw_tag, str) and raw_tag.strip() else None
                self.new_region_from_active_selection(tag=region_tag, skip_digestion=True)
            elif action == "toggle_region_visibility":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("toggle_region_visibility requires non-empty tag.")
                region = self._regions.get(tag.strip())
                if region is None:
                    raise ValueError(f"No region found with tag {tag!r}.")
                if region.hidden:
                    region.show(skip_digestion=True)
                else:
                    region.hide(skip_digestion=True)
            elif action == "delete_region":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("delete_region requires non-empty tag.")
                region = self._regions.get(tag.strip())
                if region is None:
                    raise ValueError(f"No region found with tag {tag!r}.")
                region.delete(skip_digestion=True)
            elif action == "rename_region":
                tag = content.get("tag")
                new_tag = content.get("new_tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("rename_region requires non-empty tag.")
                if not isinstance(new_tag, str) or new_tag.strip() == "":
                    raise ValueError("rename_region requires non-empty new_tag.")
                region = self._regions.get(tag.strip())
                if region is None:
                    raise ValueError(f"No region found with tag {tag!r}.")
                region.rename(new_tag.strip(), skip_digestion=True)
            elif action == "create_section_from_selection":
                atom_indices = list(self.active_selection.atom_indices)
                if len(atom_indices) == 0:
                    raise ValueError("create_section_from_selection requires a non-empty active selection.")
                coords = self._molsys.structures.get_coordinates(
                    indices=atom_indices,
                    structure_indices=[0],
                    skip_digestion=True,
                )
                # coords shape: (1, n_atoms, 3) in nm
                arr = puw.get_value(coords)
                centroid = arr[0].mean(axis=0).tolist()
                raw_fwd = content.get("camera_forward")
                if isinstance(raw_fwd, (list, tuple)) and len(raw_fwd) == 3:
                    normal = [float(v) for v in raw_fwd]
                else:
                    normal = [0.0, 0.0, -1.0]
                n = np.array(normal, dtype=float)
                length = float(np.linalg.norm(n))
                if length > 1e-8:
                    n = n / length
                normal = n.tolist()
                self.scene.add_section(point=centroid, normal=normal)
            elif action == "remove_selection":
                atom_indices = list(self.active_selection.atom_indices)
                if len(atom_indices) == 0:
                    raise ValueError("remove_selection requires a non-empty active selection.")
                self.remove(selection=atom_indices, skip_digestion=True)
                self.active_selection.clear(skip_digestion=True)
            elif action == "activate_selection":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("activate_selection requires non-empty tag.")
                self.selections.activate(tag.strip(), skip_digestion=True)
            elif action == "save_selection":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("save_selection requires non-empty tag.")
                self.active_selection.save(tag=tag.strip(), skip_digestion=True)
            elif action == "add_label_from_selection":
                text = content.get("text")
                if not isinstance(text, str) or text.strip() == "":
                    raise ValueError("add_label_from_selection requires non-empty text.")
                raw_style = content.get("label_style")
                label_style = dict(raw_style) if isinstance(raw_style, dict) else None
                self.annotations.add_label_from_active_selection(
                    text=text.strip(), label_style=label_style, skip_digestion=True
                )
            elif action == "delete_annotation":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("delete_annotation requires non-empty tag.")
                self.annotations.delete(tag.strip(), skip_digestion=True)
            elif action == "delete_shape":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("delete_shape requires non-empty tag.")
                layer = self._layers.get(tag.strip())
                if layer is None:
                    raise ValueError(f"No layer found for shape tag {tag!r}.")
                layer.delete(skip_digestion=True)
            elif action == "delete_measurement":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("delete_measurement requires non-empty tag.")
                layer = self._layers.get(tag.strip())
                if layer is None:
                    raise ValueError(f"No layer found for measurement tag {tag!r}.")
                layer.delete(skip_digestion=True)
            elif action == "hide_measurement":
                tag = content.get("tag")
                if not isinstance(tag, str) or tag.strip() == "":
                    raise ValueError("hide_measurement requires non-empty tag.")
                layer = self._layers.get(tag.strip())
                if layer is None:
                    raise ValueError(f"No layer found for measurement tag {tag!r}.")
                layer.hide(skip_digestion=True)
        elif event == "section_moved":
            tag = content.get("tag")
            raw_point = content.get("point")
            raw_normal = content.get("normal")
            if isinstance(tag, str) and tag.strip():
                tag = tag.strip()
                for record in self._section_history:
                    if record.get("tag") == tag:
                        if isinstance(raw_point, (list, tuple)) and len(raw_point) == 3:
                            record["point"] = [float(v) for v in raw_point]
                        if isinstance(raw_normal, (list, tuple)) and len(raw_normal) == 3:
                            record["normal"] = [float(v) for v in raw_normal]
                        break
        elif event == "interaction_active_selection_changed":
            self._last_active_selection_event = dict(content)
        elif event == "interaction_tool_state":
            self._last_tool_state_event = dict(content)
        elif event == "interaction_measurement_created":
            self.measurements._register_interactive_measurement(dict(content))  # noqa: SLF001
        elif event == "trajectory_frame_changed":
            # Emitted by TS when playback stops; update Python-side frame index and NPT box.
            frame = content.get("frame", 0)
            self._current_structure_index = int(frame)
            self.player._is_playing = False  # noqa: SLF001  # keep Python flag in sync
            if self._box_record is not None:
                self.show_box(
                    color=self._box_record["color"],
                    width=self._box_record["width"],
                    alpha=self._box_record["alpha"],
                    structure_indices=int(frame),
                    skip_digestion=True,
                )
        elif event == "panel_mode_state":
            self._last_panel_mode_state_event = dict(content)
        elif event == "panel_navigate":
            addon_name = content.get("addon")
            panel_id = content.get("panel")
            if isinstance(addon_name, str) and isinstance(panel_id, str):
                self._mount_addon_panel(addon_name.strip(), panel_id.strip())
        elif event == "panel_unmount":
            self._unmount_addon_panel()
        elif event == "addon_panel_action":
            if self._active_panel_widget is not None:
                _, _, widget = self._active_panel_widget
                msg_content = content.get("content")
                if isinstance(msg_content, dict):
                    widget._route_frontend_message(widget, msg_content, [])  # noqa: SLF001
        elif event == "viewer_init_failed":
            reason = content.get("reason", "unknown")
            message = content.get("message") or "Mol* viewer failed to initialize."
            emit_from_catalog(
                CATALOG["viewer_init_failed"],
                package_root=PACKAGE_ROOT,
                meta=META,
                extra={"reason": reason, "message": message},
            )

    # --- Regions / Layers registry ---

    @property
    def current_structure_index(self) -> int:
        """Index of the structure currently displayed.

        Delegate to ``view.player.index``.
        """
        return self._current_structure_index

    @property
    def regions(self) -> Mapping[str, Region]:
        """Public registry of regions (structural selections)."""
        return self._regions

    @property
    def js_logs(self) -> list[dict[str, str]]:
        """Logs received from the frontend when `debug_js` is enabled."""
        return list(self._js_logs)

    @property
    def layers(self) -> Mapping[str, Layer]:
        """Public registry of layers (non-structural visuals)."""
        return self._layers

    @property
    def selections_registry(self) -> Mapping[str, Selection]:
        """Public registry of persistent named selection wrappers."""
        return self._selections

    @property
    def molsys(self):
        """Read-only handle to the loaded MolSysMT molecular system.

        This property exposes the underlying `molsysmt.MolSys` instance created
        when you call `load(...)`. It is intended for inspection (for example,
        via `molsysmt.info(...)` or `molsysmt.select(...)`).

        Notes
        -----
        - This is a read-only property (no setter): you cannot reassign it.
        - The returned object may be mutable. If you modify it directly, you can
          desynchronize what you see in the viewer. If you need to change the
          system, modify your data and call `load(...)` again.
        """
        return self._molsys

    def _next_region_tag(self) -> str:
        self._region_counter += 1
        return f"region{self._region_counter}"

    def _next_annotation_tag(self) -> str:
        while True:
            self._annotation_counter += 1
            tag = f"annotation{self._annotation_counter}"
            if tag not in self._scene_objects:
                return tag

    def _next_layer_tag(self) -> str:
        self._layer_counter += 1
        return f"layer{self._layer_counter}"

    def _next_measurement_tag(self) -> str:
        self._measurement_counter += 1
        return f"measurement{self._measurement_counter}"

    def _next_shape_tag(self) -> str:
        self._shape_counter += 1
        return f"shape{self._shape_counter}"

    def _reset_load_blocks(self) -> None:
        self._load_blocks = []
        self._empty = True

    @property
    def load_blocks(self) -> list[dict]:
        """Read-only list of load records for every successful load operation.

        Each entry is a dict with keys ``index``, ``label``, ``start``, ``stop``,
        and ``n_atoms``.  Returns a shallow copy so the internal accounting cannot
        be mutated accidentally.
        """
        return list(self._load_blocks)



    def _get_input_n_atoms(
        self,
        molecular_system: Any,
        *,
        selection: Any = "all",
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
    ) -> int:
        return int(
            msm.get(
                molecular_system,
                element="system",
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
                n_atoms=True,
                skip_digestion=True,
            )
        )

    def _input_has_topology(self, molecular_system: Any) -> bool:
        for attribute in ("atom_id", "group_index", "bonded_atom_pairs"):
            try:
                if bool(msm.has_attribute(molecular_system, attribute, include_none=True, skip_digestion=True)):
                    return True
            except Exception:
                continue
        return False

    def _auto_load_mode(
        self,
        molecular_system: Any,
        *,
        selection: Any = "all",
        structure_indices: Any = "all",
        syntax: str = "MolSysMT",
    ) -> str:
        if self._molsys is None:
            return "replace"

        current_n_atoms = self._molsys.get_n_atoms()
        incoming_n_atoms = self._get_input_n_atoms(
            molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
        )

        if incoming_n_atoms != current_n_atoms:
            return "add"

        if not self._input_has_topology(molecular_system):
            return "append_structures"

        same_topology = bool(
            msm.compare(
                self._molsys,
                molecular_system,
                selection="all",
                structure_indices="all",
                selection_2=selection,
                structure_indices_2=structure_indices,
                syntax=syntax,
                attribute_type="topological",
                output_type="boolean",
                include_none=True,
                skip_digestion=True,
            )
        )
        return "append_structures" if same_topology else "add"

    def _register_initial_load_block(self, *, n_atoms: int, label: str | None = None) -> None:
        normalized_label = label.strip() if isinstance(label, str) and label.strip() else None
        self._load_blocks = [
            {
                "index": 0,
                "label": normalized_label,
                "n_atoms": int(n_atoms),
                "start": 0,
                "stop": int(n_atoms),
                "region_tag": None,
            }
        ]
        self._empty = False

    def _append_load_block(self, *, n_atoms: int, label: str | None = None) -> dict[str, Any]:
        normalized_label = label.strip() if isinstance(label, str) and label.strip() else None
        start = 0
        if self._load_blocks:
            start = int(self._load_blocks[-1]["stop"])
        block = {
            "index": len(self._load_blocks),
            "label": normalized_label,
            "n_atoms": int(n_atoms),
            "start": start,
            "stop": start + int(n_atoms),
            "region_tag": None,
        }
        self._load_blocks.append(block)
        self._empty = False
        return block

    def _collapse_load_blocks_to_current_whole(self) -> None:
        if self._molsys is None:
            self._reset_load_blocks()
            return
        self._register_initial_load_block(n_atoms=self._molsys.get_n_atoms(), label=self._last_label)

    def _load_region_base_tag(self, block: Mapping[str, Any]) -> str:
        label = block.get("label")
        if isinstance(label, str) and label.strip():
            return self._slugify_region_tag(label)
        load_index = int(block.get("index", 0)) + 1
        return f"Load{load_index}"

    def _ensure_load_regions_after_addition(self) -> None:
        if len(self._load_blocks) < 2:
            return

        used_tags = set(self._regions.keys())
        for block in self._load_blocks:
            if block.get("region_tag") is not None:
                continue
            start = int(block["start"])
            stop = int(block["stop"])
            atom_indices = list(range(start, stop))
            if len(atom_indices) == 0:
                continue
            base_tag = self._load_region_base_tag(block)
            tag = self._unique_region_tag(base_tag, used_tags)
            used_tags.add(tag)
            self.new_region(
                atom_indices=atom_indices,
                tag=tag,
                skip_digestion=True,
            )
            block["region_tag"] = tag

    def _slugify_region_tag(self, value: str) -> str:
        text = re.sub(r"[^A-Za-z0-9]+", "_", str(value)).strip("_")
        return text or self._next_region_tag()

    def _unique_region_tag(self, base: str, used_tags: set[str] | None = None) -> str:
        used = set(self._regions.keys()) if used_tags is None else set(used_tags) | set(self._regions.keys())
        if base not in used:
            return base
        counter = 2
        candidate = f"{base}__{counter}"
        while candidate in used:
            counter += 1
            candidate = f"{base}__{counter}"
        return candidate

    def _label_for_split_region(self, *, element_label: str, item_index: int) -> str | None:
        template = "{name}"
        element = element_label
        if element_label not in {"chain", "molecule", "entity"}:
            return None
        try:
            label = msm.get_label(
                self._molsys,
                element=element,
                selection=[item_index],
                string=template,
                skip_digestion=True,
            )
        except Exception:
            return None
        if isinstance(label, str) and label.strip():
            return label
        return None

    def _split_into_regions(
        self,
        *,
        selection: str | Any,
        structure_indices: str | Any,
        syntax: str,
        element_label: str,
        index_attribute: str,
        representation: str | None = None,
    ) -> dict[str, Region]:
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before splitting into regions.")

        atom_indices = self.select(
            selection=selection,
            structure_indices=structure_indices,
            element="atom",
            syntax=syntax,
            skip_digestion=True,
        )
        if not atom_indices:
            return {}

        get_kwargs: dict[str, Any] = {index_attribute: True}
        values = msm.get(
            self._molsys,
            element="atom",
            selection=atom_indices,
            output_type="dictionary",
            skip_digestion=True,
            **get_kwargs,
        )
        raw_indices = list(values.get(index_attribute, []))

        buckets: dict[int, dict[str, Any]] = {}
        for atom_index, item_index in zip(atom_indices, raw_indices):
            try:
                normalized_index = int(item_index)
            except Exception:
                continue
            bucket = buckets.setdefault(normalized_index, {"atom_indices": []})
            bucket["atom_indices"].append(int(atom_index))

        created: dict[str, Region] = {}
        used_tags: set[str] = set()
        for item_index in sorted(buckets):
            bucket = buckets[item_index]
            label = self._label_for_split_region(element_label=element_label, item_index=item_index)
            if isinstance(label, str) and label.strip():
                slug = self._slugify_region_tag(label)
                if element_label == "chain":
                    base_tag = slug
                else:
                    base_tag = f"{element_label}_{slug}"
            else:
                base_tag = f"{element_label}_{item_index}"
            tag = self._unique_region_tag(base_tag, used_tags)
            used_tags.add(tag)
            created[tag] = self.new_region(
                atom_indices=bucket["atom_indices"],
                tag=tag,
                representation=representation,
                skip_digestion=True,
            )
        return created

    def _normalize_representation_type(self, value: str | None) -> str | None:
        return normalize_representation_type(value)

    def _normalize_representation_preset(self, value: str | None) -> str | None:
        return normalize_representation_preset(value)

    @property
    def representations(self) -> list[str]:
        """Sorted list of allowed representation type identifiers."""
        from .representations import ALLOWED_REPRESENTATIONS
        return sorted(ALLOWED_REPRESENTATIONS)

    @property
    def presets(self) -> list[str]:
        """Sorted list of allowed preset identifiers (built-in and user-defined)."""
        from .presets import ALLOWED_PRESETS
        from ..config.user_presets import user_presets
        return sorted(ALLOWED_PRESETS | set(user_presets.keys()))

    def _unregister_region(self, tag: str) -> None:
        self._regions.pop(tag, None)

    def _resolve_user_preset(self, preset: str | None):
        return resolve_user_preset(self, preset)

    @dep_digest('molsysmt')
    @signal(tags=["region"])
    @digest()
    def new_region(
        self,
        selection: str | Any = "all",
        *,
        atom_indices: list[int] | None = None,
        tag: str | None = None,
        representation: str | None = None,
        complement_of_regions: str | list[str] | None = None,
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> Region:
        """Create a new region (structural subset) with an optional representation.

        Parameters
        ----------
        selection
            MolSysMT selection string/expression. Ignored if ``atom_indices`` is provided.
        atom_indices
            Explicit atom indices for the region (bypasses selection). If not provided,
            they are computed from ``selection`` when possible.
        tag
            Optional tag for the region. Auto-generated if omitted.
        representation
            Optional representation type (normalized and validated).
        complement_of_regions
            Tags of regions to exclude. If "all"/"All"/"ALL", the region covers the
            complement of all existing regions. Ignored if ``atom_indices`` is set.
        syntax
            Selection syntax understood by MolSysMT.

        Notes
        -----
        Requires a loaded molecular system. Call ``load(...)`` before creating regions.
        When using ``complement_of_regions``, the union of those regions' atom indices
        is removed from the full system to build the new region. Region indices are
        taken from their stored `atom_indices` (acks) when available.
        """
        tag = tag or self._next_region_tag()
        representation = self._normalize_representation_type(representation)

        # Compute atom_indices if not provided
        if atom_indices is None and complement_of_regions is not None:
            region_tags = []
            if isinstance(complement_of_regions, str):
                if complement_of_regions.lower() == "all":
                    region_tags = list(self._regions.keys())
                else:
                    region_tags = [complement_of_regions]
            else:
                region_tags = list(complement_of_regions)
            exclude: set[int] = set()
            for rt in region_tags:
                r = self._regions.get(rt)
                if r and r.atom_indices is not None:
                    exclude.update(r.atom_indices)
            if self._molsys is None:
                raise ValueError("Cannot build complement: no molecular system loaded.")
            total = int(self._molsys._get_n_atoms())  # type: ignore[attr-defined]
            atom_indices = [i for i in range(total) if i not in exclude]
        elif atom_indices is None and self._molsys is not None:
            atom_indices = list(msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True))
        elif atom_indices is None and self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before creating regions.")

        if atom_indices is None or len(atom_indices) == 0:
            raise ValueError("Cannot create region: empty atom_indices for selection.")

        region = Region(
            self,
            tag,
            selection,
            atom_indices=atom_indices,
            representation=representation,
            repr_params=repr_params,
        )
        self._regions[tag] = region
        region._send_create()  # noqa: SLF001
        if representation is not None or repr_params:
            region.set_representation(
                representation,
                skip_digestion=True,
                **repr_params,
            )
        return region

    @signal(tags=["region", "selection"])
    @digest()
    def new_region_from_active_selection(
        self,
        *,
        tag: str | None = None,
        representation: str | None = None,
        skip_digestion: bool = False,
        **repr_params: Any,
    ) -> Region:
        """Create a region from the last active selection event.

        This is the first explicit bridge from interactive exploration to
        reproducible viewer state. The current implementation is intentionally
        narrow and derives the region from the stored selection atom indices.
        """
        event = self.get_last_active_selection_event()
        if event is None:
            raise ValueError("No active selection stored. Select an element before creating a region.")

        atom_indices = event.get("atom_indices") or []
        atom_indices = [int(ii) for ii in atom_indices]
        if len(atom_indices) == 0:
            raise ValueError("The current active selection does not resolve to any atoms.")

        return self.new_region(
            atom_indices=atom_indices,
            tag=tag,
            representation=representation,
            skip_digestion=True,
            **repr_params,
        )

    @signal(tags=["layer"])
    @digest()
    def new_layer(
        self,
        *,
        tag: str | None = None,
        kind: str | None = None,
        skip_digestion: bool = False,
        **meta: Any,
    ) -> Layer:
        """Create a new layer (non-structural visual group)."""
        tag = tag or self._next_layer_tag()
        tag = self._assert_nonstructural_tag_available(tag)
        layer = Layer(self, tag, kind=kind, meta=meta)
        self._layers[tag] = layer
        layer._send_create()  # noqa: SLF001
        return layer

    @signal(tags=["region", "split"])
    @digest()
    def make_regions_by(
        self,
        element: str,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        *,
        representation: str | None = None,
        skip_digestion: bool = False,
    ) -> dict[str, Region]:
        """Create one region per selected hierarchy element and return them by tag."""
        representation = self._normalize_representation_type(representation)
        allowed = {
            "chain": "chain_index",
            "molecule": "molecule_index",
            "entity": "entity_index",
        }
        if element not in allowed:
            raise ValueError(f"Unsupported element for make_regions_by: {element!r}. Allowed: {sorted(allowed)}")
        return self._split_into_regions(
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            element_label=element,
            index_attribute=allowed[element],
            representation=representation,
        )

    @signal(tags=["viewer", "controls"], extra_factory=_controls_signal_extra)
    @digest()
    def set_controls_visible(
        self,
        visible: bool,
        *,
        autohide: bool | None = None,
        position: list[str] | tuple[str, str] | None = None,
        position_fullscreen: list[str] | tuple[str, str] | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Show or hide the on-canvas controls (reset/full/bg/spin/swing + trajectory bar). Optionally toggle autohide and positions."""
        try:
            self.widget.show_controls = bool(visible)
            if autohide is not None:
                self.widget.autohide_controls = bool(autohide)
            if position is not None:
                self.widget.controls_position = list(position)
            if position_fullscreen is not None:
                self.widget.controls_position_fullscreen = list(position_fullscreen)
        except Exception:
            pass

    @signal(tags=["viewer", "panel"], extra_factory=_panel_mode_signal_extra)
    @digest()
    def set_panel_mode(
        self,
        panel: str | None = None,
        *,
        expanded: bool = True,
        skip_digestion: bool = False,
    ) -> None:
        """Open/close the shared panel-mode surface.

        Parameters
        ----------
        panel
            One of ``"navigate"`` or ``"workbench"``. If ``None``, the frontend
            may use its remembered last panel when opening.
        expanded
            If ``True`` (default), open the requested panel. If ``False``,
            collapse the current panel-mode surface.
        """
        self._send(
            {
                "op": "set_panel_mode",
                "panel": panel,
                "expanded": bool(expanded),
            }
        )

    @signal(tags=["viewer", "panel"], extra_factory=_workspace_signal_extra)
    @digest()
    def set_workspace(
        self,
        workspace: str = "core",
        *,
        skip_digestion: bool = False,
    ) -> None:
        """Select the active workspace in the shared panel-mode runtime.

        Parameters
        ----------
        workspace
            Workspace identifier such as ``"core"`` or an add-on workspace id.
        """
        self._send(
            {
                "op": "set_workspace",
                "workspace": workspace,
            }
        )

    @signal(tags=["viewer", "panel"], extra_factory=_workspace_panel_signal_extra)
    @digest()
    def set_workspace_panel(
        self,
        panel: str,
        *,
        workspace: str | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Select the active panel inside the current or given workspace.

        Parameters
        ----------
        panel
            Panel identifier inside the target workspace.
        workspace
            Optional workspace identifier. If omitted, the frontend uses the
            current workspace. When set to ``"core"``, ``"navigate"`` and
            ``"workbench"`` remain the meaningful panel ids.
        """
        self._send(
            {
                "op": "set_workspace_panel",
                "panel": panel,
                "workspace": workspace,
            }
        )

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_catalog_signal_extra)
    @digest()
    def workspace_catalog(self, *, skip_digestion: bool = False) -> list[dict[str, Any]]:
        """Return the current effective workspace catalog visible to the view."""
        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        workbench_specs = self.addons.workbench_section_specs(skip_digestion=True)
        context_action_specs = self.addons.context_action_specs(skip_digestion=True)
        export_helper_specs = self.addons.export_helper_specs(skip_digestion=True)
        state = self.get_panel_mode_state() or {}
        active_workspace = state.get("workspace") if isinstance(state, dict) else None

        records: list[dict[str, Any]] = [
            {
                "id": "core",
                "title": "Core",
                "subtitle": "Navigate + Workbench",
                "active": active_workspace == "core",
            }
        ]

        for workspace in workspace_specs:
            workspace_id = workspace.get("id")
            addon_name = workspace.get("addon")
            if not isinstance(workspace_id, str) or not isinstance(addon_name, str):
                continue
            panel_count = sum(
                1
                for item in panel_specs
                if item.get("addon") == addon_name and item.get("target", "panel_mode") == "panel_mode"
            )
            workbench_section_count = sum(
                1
                for item in workbench_specs
                if item.get("addon") == addon_name and item.get("target_panel", "workbench") == "workbench"
            )
            context_action_count = sum(1 for item in context_action_specs if item.get("addon") == addon_name)
            export_helper_count = sum(1 for item in export_helper_specs if item.get("addon") == addon_name)
            total_visible = panel_count + workbench_section_count
            if total_visible <= 0:
                continue

            summary_parts: list[str] = []
            if panel_count > 0:
                summary_parts.append(f"{panel_count} panel{'' if panel_count == 1 else 's'}")
            if workbench_section_count > 0:
                summary_parts.append(f"{workbench_section_count} section{'' if workbench_section_count == 1 else 's'}")
            if context_action_count > 0:
                summary_parts.append(f"{context_action_count} context action{'' if context_action_count == 1 else 's'}")
            if export_helper_count > 0:
                summary_parts.append(f"{export_helper_count} export helper{'' if export_helper_count == 1 else 's'}")

            record = dict(workspace)
            record["subtitle"] = " · ".join(summary_parts)
            record["active"] = workspace_id == active_workspace
            records.append(record)

        return records

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_panels_signal_extra)
    @digest()
    def workspace_panels(
        self,
        workspace: str = "core",
        *,
        skip_digestion: bool = False,
    ) -> list[dict[str, Any]]:
        """Return the visible local panel stack for a workspace."""
        state = self.get_panel_mode_state() or {}
        active_workspace = state.get("workspace") if isinstance(state, dict) else None
        active_panel = state.get("workspace_panel") if isinstance(state, dict) else None
        if workspace == "core":
            return [
                {"id": "navigate", "title": "Navigate", "active": active_workspace == "core" and active_panel == "navigate"},
                {"id": "workbench", "title": "Workbench", "active": active_workspace == "core" and active_panel == "workbench"},
            ]

        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        addon_name = next(
            (
                item.get("addon")
                for item in workspace_specs
                if item.get("id") == workspace and isinstance(item.get("addon"), str)
            ),
            None,
        )
        if not isinstance(addon_name, str):
            return []

        records: list[dict[str, Any]] = []
        for item in panel_specs:
            if item.get("addon") != addon_name:
                continue
            if item.get("target", "panel_mode") != "panel_mode":
                continue
            records.append(
                {
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "entry": item.get("entry"),
                    "addon": addon_name,
                    "workspace": workspace,
                    "active": active_workspace == workspace and item.get("id") == active_panel,
                }
            )
        return records

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_sections_signal_extra)
    @digest()
    def workspace_sections(
        self,
        workspace: str = "core",
        *,
        skip_digestion: bool = False,
    ) -> list[dict[str, Any]]:
        """Return the visible workbench sections for a workspace."""
        if workspace == "core":
            return []

        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        workbench_specs = self.addons.workbench_section_specs(skip_digestion=True)
        addon_name = next(
            (
                item.get("addon")
                for item in workspace_specs
                if item.get("id") == workspace and isinstance(item.get("addon"), str)
            ),
            None,
        )
        if not isinstance(addon_name, str):
            return []

        records: list[dict[str, Any]] = []
        for item in workbench_specs:
            if item.get("addon") != addon_name:
                continue
            if item.get("target_panel", "workbench") != "workbench":
                continue
            section_id = item.get("id")
            title = item.get("title")
            if not isinstance(section_id, str) or not isinstance(title, str):
                continue
            record = dict(item)
            record["workspace"] = workspace
            records.append(record)
        return self._enrich_workbench_sections(records)

    @signal(tags=["viewer", "panel", "query"], extra_factory=_workspace_runtime_signal_extra)
    @digest()
    def workspace_runtime(self, *, pretty: bool = False, skip_digestion: bool = False) -> dict[str, Any] | str:
        """Return a notebook-friendly snapshot of the shared workspace runtime."""
        state = self.get_panel_mode_state() or {}
        if not isinstance(state, dict):
            state = {}
        current_workspace = state.get("workspace")
        if not isinstance(current_workspace, str) or current_workspace.strip() == "":
            current_workspace = "core"
        workspaces = self.workspace_catalog(skip_digestion=True)
        current_panels = self.workspace_panels(current_workspace, skip_digestion=True)
        current_sections = self.workspace_sections(current_workspace, skip_digestion=True)
        current_panel = next((item for item in current_panels if item.get("active") is True), None)
        current_workspace_record = next((item for item in workspaces if item.get("id") == current_workspace), None)
        payload = {
            "state": dict(state),
            "workspaces": workspaces,
            "current_workspace": current_workspace,
            "current_workspace_record": current_workspace_record,
            "current_panels": current_panels,
            "current_panel": current_panel,
            "current_sections": current_sections,
        }
        if pretty:
            return json.dumps(payload, indent=2, sort_keys=True)
        return payload

    @property
    def visible_atom_indices(self):
        """Return the indices of currently visible atoms."""
        if self.atom_mask is None:
            return None
        # Use a plain list so the payload is JSON-serializable.
        return np.nonzero(self.atom_mask)[0].tolist()

    @property
    def visible_structure_indices(self):
        """Return the indices of currently visible structures."""
        if self.structure_mask is None:
            return None
        # Use a plain list so the payload is JSON-serializable.
        return np.nonzero(self.structure_mask)[0].tolist()

    def _update_visibility_in_frontend(self):
        if self.atom_mask is None:
            return
        self._send({
            "op": "update_visibility",
            "options": {"visible_atom_indices": self.visible_atom_indices},
        })

    def _invoke_addon_entry(self, entry: str) -> Any | None:
        candidate = _resolve_entry_callable(entry)
        if candidate is None or not callable(candidate):
            return None
        try:
            signature = inspect.signature(candidate)
        except (TypeError, ValueError):
            signature = None

        if signature is not None and len(signature.parameters) == 0:
            return candidate()

        try:
            return candidate(self)
        except TypeError:
            try:
                return candidate(view=self)
            except TypeError:
                return None

    def _materialize_addon_entry_payload(self, entry: Any) -> dict[str, Any] | None:
        if not isinstance(entry, str) or entry.strip() == "":
            return None
        payload = self._invoke_addon_entry(entry)
        if payload is None:
            return None
        if isinstance(payload, dict):
            return dict(payload)
        return {"value": payload}

    def _enrich_workbench_sections(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in records:
            record = dict(item)
            payload = self._materialize_addon_entry_payload(record.get("entry"))
            if payload is not None:
                record["runtime_payload"] = payload
                if isinstance(payload.get("key"), str):
                    record["key"] = payload["key"]
                if isinstance(payload.get("item_title"), str):
                    record["item_title"] = payload["item_title"]
                if isinstance(payload.get("item_subtitle"), str):
                    record["item_subtitle"] = payload["item_subtitle"]
            enriched.append(record)
        return enriched

    def _enrich_export_helper_specs(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in records:
            record = dict(item)
            payload = self._materialize_addon_entry_payload(record.get("entry"))
            if payload is not None:
                record["runtime_payload"] = payload
            enriched.append(record)
        return enriched

    def _build_addon_runtime_summary_message(self) -> dict[str, Any]:
        addon_names = self.addons.enabled(skip_digestion=True)
        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        workbench_sections = self._enrich_workbench_sections(
            self.addons.workbench_section_specs(skip_digestion=True)
        )
        context_action_specs = self.addons.context_action_specs(skip_digestion=True)
        export_helper_specs = self._enrich_export_helper_specs(
            self.addons.export_helper_specs(skip_digestion=True)
        )
        return {
            "op": "set_addon_runtime_summary",
            "addons": addon_names,
            "workspace_specs": workspace_specs,
            "panel_specs": panel_specs,
            "workbench_sections": workbench_sections,
            "context_action_specs": context_action_specs,
            "export_helper_specs": export_helper_specs,
        }

    def _sync_addons_runtime(self) -> None:
        self._send(self._build_addon_runtime_summary_message())

    def _mount_addon_panel(self, addon_name: str, panel_id: str) -> None:
        self._unmount_addon_panel()
        widget = self.addons.resolve_panel_widget(addon_name, panel_id)
        if widget is None:
            return

        # Route push_state and all sends through the viewer's comm channel
        def _routed_send(msg: dict, buffers: Any = None) -> None:
            self._send_runtime_only({
                "op": "addon_panel_message",
                "addon": addon_name,
                "panel": panel_id,
                "content": msg,
            })

        widget.send = _routed_send  # type: ignore[method-assign]
        self._active_panel_widget = (addon_name, panel_id, widget)

        widget.on_mount(self)

        # Push initial context to panel JS
        ctx = widget._build_viewer_context()  # noqa: SLF001
        _routed_send({"type": "context", "context": ctx})

        # Tell TS canvas to mount the panel ESM
        self._send_runtime_only({
            "op": "mount_addon_panel",
            "addon": addon_name,
            "panel": panel_id,
            "esm": widget._esm,  # noqa: SLF001
            "css": getattr(widget, "_css", "") or "",
        })

    def _unmount_addon_panel(self) -> None:
        if self._active_panel_widget is None:
            return
        _, _, widget = self._active_panel_widget
        self._active_panel_widget = None
        try:
            widget.on_unmount(self)
        except Exception:
            pass

    def _remap_indices(self, indices: Any, atom_index_map: dict[int, int] | None) -> list[int]:
        if atom_index_map is None:
            if isinstance(indices, list):
                return [int(ii) for ii in indices if isinstance(ii, (int, np.integer))]
            return []
        if not isinstance(indices, list):
            return []
        out: list[int] = []
        for ii in indices:
            if not isinstance(ii, (int, np.integer)):
                continue
            mapped = atom_index_map.get(int(ii))
            if mapped is None:
                continue
            out.append(mapped)
        return out

    def _remap_atom_pairs(self, pairs: Any, atom_index_map: dict[int, int] | None) -> list[list[int]] | None:
        if atom_index_map is None:
            return pairs if isinstance(pairs, list) else None
        if not isinstance(pairs, list):
            return None
        out: list[list[int]] = []
        for pair in pairs:
            if (
                isinstance(pair, (list, tuple))
                and len(pair) == 2
                and isinstance(pair[0], (int, np.integer))
                and isinstance(pair[1], (int, np.integer))
            ):
                a = atom_index_map.get(int(pair[0]))
                b = atom_index_map.get(int(pair[1]))
                if a is None or b is None:
                    continue
                out.append([a, b])
        return out

    def _remap_shape_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict | None:
        if atom_index_map is None:
            return msg
        op = msg.get("op")
        if not isinstance(op, str) or not op.startswith("add_"):
            return msg

        remapped = dict(msg)
        options = remapped.get("options")
        if not isinstance(options, dict):
            return remapped

        options = dict(options)
        remapped["options"] = options

        if "atom_indices" in options:
            options["atom_indices"] = self._remap_indices(options.get("atom_indices"), atom_index_map)
            if not options["atom_indices"]:
                return None

        if "atom_pairs" in options:
            options["atom_pairs"] = self._remap_atom_pairs(options.get("atom_pairs"), atom_index_map)
            if options["atom_pairs"] == []:
                return None

        if "mouth_atom_indices" in options:
            mouths = options.get("mouth_atom_indices")
            if isinstance(mouths, list) and mouths and isinstance(mouths[0], list):
                options["mouth_atom_indices"] = [
                    self._remap_indices(m, atom_index_map) for m in mouths
                ]
            else:
                options["mouth_atom_indices"] = self._remap_indices(mouths, atom_index_map)

        return remapped

    def _remap_measurement_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict | None:
        if atom_index_map is None:
            return msg
        op = msg.get("op")
        if op not in {"add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return msg

        remapped = dict(msg)
        options = remapped.get("options")
        if not isinstance(options, dict):
            return remapped
        options = dict(options)
        remapped["options"] = options
        picks = options.get("picks_atom_indices")
        if not isinstance(picks, list):
            return remapped
        remapped_picks = [self._remap_indices(pick, atom_index_map) for pick in picks]
        if any(len(pick) == 0 for pick in remapped_picks):
            return None
        options["picks_atom_indices"] = remapped_picks
        endpoint_atom_indices = options.get("endpoint_atom_indices")
        if isinstance(endpoint_atom_indices, list):
            remapped_endpoint_atoms = [self._remap_indices(pick, atom_index_map) for pick in endpoint_atom_indices]
            if any(
                len(original) > 0 and len(remapped_pick) == 0
                for original, remapped_pick in zip(endpoint_atom_indices, remapped_endpoint_atoms)
            ):
                return None
            options["endpoint_atom_indices"] = remapped_endpoint_atoms
        return remapped

    def _remap_selection_message(self, msg: dict, atom_index_map: dict[int, int] | None) -> dict | None:
        if atom_index_map is None:
            return msg
        if msg.get("op") != "save_selection":
            return msg
        atom_indices = msg.get("atom_indices")
        if not isinstance(atom_indices, list):
            return dict(msg)
        remapped = self._remap_indices(atom_indices, atom_index_map)
        if len(remapped) == 0:
            return None
        updated = dict(msg)
        updated["atom_indices"] = remapped
        return updated

    def _rebuild_view_from_current_molsys(
        self,
        *,
        label: str | None = None,
        atom_index_map: dict[int, int] | None = None,
        visible_atom_indices: list[int] | None = None,
    ) -> None:
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before mutating the view.")

        from ..loaders.load_molsysmt import _serialize_molsys_payload
        import molsysmt as msm

        viewer_json = self._molsys.to_form("molsysmt.ViewerJSON")

        # Extract hierarchy indices from MolSysMT to enrich the payload during rebuild
        molecule_indices = msm.get(self._molsys, element="atom", molecule_index=True, skip_digestion=True)
        component_indices = msm.get(self._molsys, element="atom", component_index=True, skip_digestion=True)
        molecule_names = msm.get(self._molsys, element="atom", molecule_name=True, skip_digestion=True)
        component_names = msm.get(self._molsys, element="atom", component_name=True, skip_digestion=True)

        payload = _serialize_molsys_payload(
            viewer_json,
            molecule_indices=molecule_indices,
            component_indices=component_indices,
            molecule_names=molecule_names,
            component_names=component_names
        )
        if payload is None:
            raise ValueError("Unable to serialize MolSysMT viewer payload")

        n_atoms = int(self._molsys.get_n_atoms())
        n_structures = len(payload.get("structures") or [])
        multiple_structures = n_structures > 1
        self.atom_mask = np.ones(n_atoms, dtype=bool)
        if visible_atom_indices is not None:
            self.atom_mask[:] = False
            keep = self._remap_indices(visible_atom_indices, atom_index_map)
            if keep:
                self.atom_mask[keep] = True

        if atom_index_map is not None:
            for region in self._regions.values():
                if region.atom_indices is None:
                    continue
                region.atom_indices = tuple(self._remap_indices(list(region.atom_indices), atom_index_map))

        # Rebuild the message history to reflect the new state (important for HTML exports).
        self._message_history = []
        self._pending_messages = []

        self._send({"op": "clear_all"})
        self._send(
            {
                "op": "load_molsys_payload",
                "payload": payload,
                "label": label,
                "multiple_structures": multiple_structures,
            }
        )

        if getattr(self.whole, "_preset", None) is not None or getattr(self.whole, "_representation", None) is not None:
            self.whole.set_representation(
                getattr(self.whole, "_representation", None),
                preset=getattr(self.whole, "_preset", None),
                skip_digestion=True,
                **getattr(self.whole, "_repr_params", {}),
            )

        if self._global_hidden:
            self._send({"op": "hide_global", "target": "global"})

        for layer in list(self._layers.values()):
            if not getattr(layer, "_active", True):
                continue
            layer._send_create()  # noqa: SLF001
            if getattr(layer, "_hidden", False):
                layer.hide(skip_digestion=True)

        for region in list(self._regions.values()):
            if not getattr(region, "_active", True):
                continue
            region._send_create()  # noqa: SLF001
            if getattr(region, "preset", None) is not None or region.representation is not None or region.repr_params:
                region.set_representation(
                    region.representation,
                    preset=getattr(region, "preset", None),
                    skip_digestion=True,
                    **(region.repr_params or {}),
                )
            if getattr(region, "_hidden", False):
                region.hide(skip_digestion=True)

        new_shape_history: list[dict] = []
        for msg in self._shape_history:
            remapped = self._remap_shape_message(msg, atom_index_map)
            if remapped is None:
                continue
            new_shape_history.append(remapped)
            self._send_replay(remapped)
        self._shape_history = new_shape_history

        new_annotation_history: list[dict] = []
        for msg in self._annotation_history:
            remapped = self._remap_shape_message(msg, atom_index_map)
            if remapped is None:
                continue
            new_annotation_history.append(remapped)
            self._send_replay(remapped)
        self._annotation_history = new_annotation_history

        new_measurement_history: list[dict] = []
        for msg in self._measurement_history:
            remapped = self._remap_measurement_message(msg, atom_index_map)
            if remapped is None:
                continue
            new_measurement_history.append(remapped)
            self._send_replay(remapped)
        self._measurement_history = new_measurement_history

        rewritten_selections: list[dict] = []
        for msg in self._selection_history:
            remapped = self._remap_selection_message(msg, atom_index_map)
            if remapped is None:
                continue
            rewritten_selections.append(remapped)
            self._send_replay(remapped)
        self._selection_history = rewritten_selections
        self._selections = {
            tag: selection
            for tag, selection in self._selections.items()
            if any(record.get("tag") == tag for record in self._selection_history)
        }

        self._update_visibility_in_frontend()

    # --- Public loading API ---

    @dep_digest('molsysmt')
    @signal(tags=["load"], extra_factory=_load_signal_extra)
    @digest()
    def load(
        self,
        molecular_system: Any,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        label: str | None = None,
        mode: str = "add",
        skip_digestion: bool = False,
    ) -> None:
        """Load a molecular system (MolSysMT-compatible) into the viewer."""
        if mode == "replace":
            self.reset_viewer(skip_digestion=True)
        elif mode == "auto":
            mode = self._auto_load_mode(
                molecular_system,
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
            )

        if self._molsys is None:
            if mode == "append_structures":
                raise ValueError(
                    "No molecular system loaded. Load a topology or full system before calling "
                    "load(..., mode='append_structures')."
                )
            _load_from_molsysmt(
                molecular_system=molecular_system,
                selection=selection,
                structure_indices=structure_indices,
                syntax=syntax,
                label=label,
                skip_digestion=True,
                view=self,
            )
            self._register_initial_load_block(n_atoms=self._molsys.get_n_atoms(), label=label)
            self._last_label = label
            return

        if mode != "add":
            if mode == "append_structures":
                self.append_structures(
                    molecular_system,
                    selection=selection,
                    structure_indices=structure_indices,
                    syntax=syntax,
                    skip_digestion=True,
                )
                return
            raise ValueError(f"Unsupported load mode: {mode!r}")

        self.add(
            molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            label=label,
            skip_digestion=True,
        )
        self._ensure_load_regions_after_addition()

    @signal(tags=["visibility"])
    @digest()
    def hide(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", skip_digestion: bool = False):
        """Hide atoms matching the given selection (MolSysMT syntax by default)."""
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Hide everything: atoms + all reps (global + regions)
            self.atom_mask[:] = False
            self._update_visibility_in_frontend()
            # Hide all representations in the frontend
            self._send({"op": "hide_global", "target": "all"})  # noqa: SLF001
        else:
            atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True)
            self.atom_mask[atom_indices] = False

        self._update_visibility_in_frontend()

    @signal(tags=["visibility"])
    @digest()
    def show(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", *, force: bool = False, skip_digestion: bool = False):
        """Show the widget (first call or if `force=True`) and optionally adjust visibility."""
        # (1) Apply visibility changes if a system is loaded
        if self._molsys is not None and self.atom_mask is not None:
            if is_all(selection) and is_all(structure_indices):
                # Reset visibility: show all atoms
                self.atom_mask[:] = True
                self._update_visibility_in_frontend()
                # Show all representations in the frontend (global + regions)
                self._send({"op": "show_global", "target": "all"})  # noqa: SLF001
                # Re-apply the user's intent about the baseline/global view
                self._send({"op": "hide_global" if self._global_hidden else "show_global", "target": "global"})  # noqa: SLF001
            elif not (is_all(selection) and is_all(structure_indices)):
                # Partial "show": turn on only the requested selection
                atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True)
                self.atom_mask[atom_indices] = True
                self._update_visibility_in_frontend()
    
        # (2) Handle first-time or forced visualisation
        if force or not self._already_shown:
            self._already_shown = True
            return self.widget
    
        # (3) Subsequent calls without force do not return the widget
        return None

    @signal(tags=["visibility"])
    @digest()
    def isolate(self, selection: str | Any = "all", structure_indices: str | Any = "all", syntax: str = "MolSysMT", skip_digestion: bool = False):
        """Show only the atoms in `selection`; hide everything else (reset if selection == 'all')."""
        if self.atom_mask is None or self._molsys is None:
            return

        if is_all(selection):
            # Isolating "all" → same as reset visibility
            self.atom_mask[:] = True
            self._update_visibility_in_frontend()
            return

        atom_indices = msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True)
        self.atom_mask[:] = False
        self.atom_mask[atom_indices] = True
        self._update_visibility_in_frontend()

    # ── Unit cell / box visualization ──────────────────────────────────────

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
        """Render the unit-cell or simulation-box edges in the canvas.

        Reads the box vectors from the first (or *structure_indices*-th) structure
        of the loaded system, converts them from nm to Å, and draws the 12 box
        edges as cylinders.  A subsequent call replaces the previous box.

        Parameters
        ----------
        color
            Edge color. Accepts any value supported by ``view.colors.normalize_color``.
        width
            Cylinder radius in Å.
        alpha
            Opacity (0 = transparent, 1 = opaque).
        structure_indices
            Which structure's box to visualise (0-based integer or ``"all"``).
            Defaults to the first structure (index 0).
        """
        from .._private.arg_digestion.argument.structure_indices import digest_structure_indices  # noqa: PLC0415

        sidx = 0 if structure_indices in ("all", None) else int(structure_indices)

        box_q = msm.get(self._molsys, element="system", box=True, skip_digestion=True)
        if box_q is None:
            raise ValueError("The loaded system does not have box information.")

        box_nm = puw.get_value(box_q)  # shape (n_structures, 3, 3) in nm
        if box_nm.ndim == 3:
            box_nm = box_nm[sidx]  # shape (3, 3)

        # Convert nm → Å
        box_a = box_nm * 10.0  # (3, 3) in Å
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

        # 12 box edges as coordinate pairs [[x0,y0,z0], [x1,y1,z1]]
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

        from ..colors import normalize_color as _nc  # noqa: PLC0415
        color_int = _nc(color)

        # Remove previous box (if any) then redraw
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
        """ID of the structure currently displayed (requires a loaded molecular system).

        Returns the ``structure_id`` value at the current frame index, or ``None``
        if no system is loaded or the system has no structure IDs.
        """
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
        """Jump to a specific structure (frame) index.

        Delegate to ``view.player.go_to_structure()``.
        """
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
        """Start playback through structures.

        Delegate to ``view.player.play()``.
        """
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
        """Pause playback.

        Delegate to ``view.player.pause()``.
        """
        self.player.pause(skip_digestion=True)

    @signal(tags=["structures"])
    @digest()
    def set_play_speed(self, fps: int, skip_digestion: bool = False) -> None:
        """Update the playback frame rate.

        Delegate to ``view.player.set_fps()``.
        """
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
        """Return atom coordinates from the loaded molecular system.

        Parameters
        ----------
        selection
            Atom selection (MolSysMT string or list of indices).
        structure_indices
            Structure indices to include (default ``"all"``).
        syntax
            Selection syntax (default ``"MolSysMT"``).

        Returns
        -------
        puw quantity
            Coordinates with shape ``(n_structures, n_atoms, 3)`` in nm.
        """
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
        """Replace atom coordinates in the loaded molecular system and update the canvas.

        Parameters
        ----------
        coordinates
            New coordinates as a puw quantity or array with shape
            ``(n_structures, n_atoms, 3)`` in nm.
        selection
            Atom selection (MolSysMT string or list of indices).
        structure_indices
            Structure indices to update (default ``"all"``).
        syntax
            Selection syntax (default ``"MolSysMT"``).
        """
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
        self._rebuild_view_from_current_molsys(
            label=self._last_label,
            visible_atom_indices=visible,
        )

    @signal(tags=["viewer"])
    @digest()
    def reset_viewer(self, skip_digestion: bool = False) -> None:
        """Fully clear the viewer and reset internal state (requires a new `load(...)`)."""
        # Reset Python-side state
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
        self._region_counter = 0
        self._annotation_counter = 0
        self._layer_counter = 0
        self._measurement_counter = 0
        self._shape_counter = 0
        self._section_counter = 0
        self._global_hidden = False
        self._box_visible = False
        self._box_record = None
        self._atom_color_map = {}
        self.whole = Whole(self)
        self._shape_history.clear()
        self._annotation_history.clear()
        self._measurement_history.clear()
        self._section_history.clear()
        self._selection_history.clear()
        self._last_label = None
        self._current_figure_spec = None
        self._current_structure_index = 0
        self._reset_load_blocks()

        # Ask frontend to clear everything (molecule + shapes + view)
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

    def export_state(self) -> dict:
        """Serialize the current viewer overlay state to a JSON-compatible dict.

        The returned dict captures annotations, measurements, saved selections,
        and regions (with resolved ``atom_indices``).  The loaded structure is
        **not** included.  Pass the dict to :meth:`import_state` to restore it
        on any viewer that has the same (or a compatible) structure loaded.

        Returns
        -------
        dict
            Keys: ``version``, ``annotations``, ``measurements``,
            ``selections``, ``regions``.
        """
        def _to_python(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _to_python(v) for k, v in obj.items()}
            if isinstance(obj, (list, tuple)):
                return [_to_python(v) for v in obj]
            try:
                import numpy as np
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
            except ImportError:
                pass
            return obj

        regions = []
        for tag, region in self._regions.items():
            if region.atom_indices is not None:
                regions.append({"tag": tag, "atom_indices": list(region.atom_indices)})

        return _to_python({
            "version": 1,
            "annotations": self.annotations.records(),
            "measurements": self.measurements.records(),
            "selections": self.selections.records(),
            "regions": regions,
        })

    def import_state(self, state: dict, *, clear_first: bool = True) -> None:
        """Restore viewer overlay state from a dict produced by :meth:`export_state`.

        The structure must already be loaded (or at least compatible with the
        ``atom_indices`` in the stored state) before calling this method.

        Parameters
        ----------
        state
            Dict produced by :meth:`export_state`.
        clear_first
            If ``True`` (default), clears all existing annotations,
            measurements, saved selections, and regions before importing.
            Set to ``False`` to merge into existing state.
        """
        if not isinstance(state, dict):
            raise TypeError(f"state must be a dict, got {type(state).__name__}.")
        version = state.get("version", 1)
        if version != 1:
            raise ValueError(f"Unsupported state version: {version!r}.")

        if clear_first:
            self.clear_decorations(labels=True, shapes=False, styles=False, skip_digestion=True)
            self.measurements.clear(skip_digestion=True)
            self.selections.clear(skip_digestion=True)
            for tag in list(self._regions):
                try:
                    self._regions[tag].delete(skip_digestion=True)
                except Exception:
                    pass

        for msg in state.get("annotations", []):
            if isinstance(msg, dict) and msg.get("op") == "add_label":
                self._send(msg)

        for msg in state.get("measurements", []):
            if isinstance(msg, dict) and msg.get("op") in (
                "add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"
            ):
                self._send(msg)

        for msg in state.get("selections", []):
            if isinstance(msg, dict) and msg.get("op") == "save_selection":
                tag = msg.get("tag")
                if tag and not self.selections.contains(tag, skip_digestion=True):
                    self._send(msg)

        if self._molsys is not None:
            for region_data in state.get("regions", []):
                tag = region_data.get("tag")
                atom_indices = region_data.get("atom_indices")
                if tag and isinstance(atom_indices, list) and len(atom_indices) > 0:
                    try:
                        self.new_region(atom_indices=atom_indices, tag=tag, skip_digestion=True)
                    except Exception:
                        pass

    @signal(tags=["viewer", "query"], extra_factory=_panel_mode_state_query_extra)
    def get_panel_mode_state(self, *, pretty: bool = False) -> dict | str | None:
        """Return the last known frontend panel/workspace runtime state.

        Parameters
        ----------
        pretty
            If ``True``, return formatted JSON instead of a dict.
        """
        if self._last_panel_mode_state_event is None:
            return None
        if not pretty:
            return dict(self._last_panel_mode_state_event)
        return json.dumps(self._last_panel_mode_state_event, indent=2, sort_keys=True)

    @signal(tags=["camera"], extra_factory=_camera_snapshot_extra)
    @digest()
    def set_camera_snapshot(self, snapshot: dict, *, duration_ms: int = 0, skip_digestion: bool = False) -> None:
        """Apply a camera snapshot. Delegate to ``view.camera.set_snapshot()``."""
        self.camera.set_snapshot(snapshot, duration_ms=duration_ms, skip_digestion=True)

    @signal(tags=["figure"])
    @digest()
    def set_figure_spec(self, figure_spec: FigureSpec, *, skip_digestion: bool = False) -> None:
        """Anchor a figure recipe to the viewer workbench Scene section.

        Sends a ``set_figure_spec`` op to the frontend so the Workbench → Scene
        section reflects the explicit figure baseline.  The spec is also stored
        for replay in HTML exports.

        Parameters
        ----------
        figure_spec
            A :class:`~molsysviewer.figures.FigureSpec` instance.
        """
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

    def _viewer_info_summary(self) -> dict[str, Any]:
        current_style = self.styles.current(skip_digestion=True) if hasattr(self, "styles") else None
        layer_tags = sorted(self._layers.keys())
        region_tags = sorted(self._regions.keys())
        shape_tags = sorted(
            tag for tag, item in self._scene_objects.items() if getattr(item, "kind", None) == "shape"
        )
        annotation_tags = sorted(self.annotations.tags)
        measurement_tags = sorted(self.measurements.tags(skip_digestion=True))
        selection_tags = sorted(self.selections.tags)

        return {
            "whole": {
                "representation": getattr(self.whole, "_representation", None),
                "preset": getattr(self.whole, "_preset", None),
                "params": dict(getattr(self.whole, "_repr_params", {}) or {}),
                "visible": not bool(self._global_hidden),
            },
            "loads": [
                {
                    "index": b.get("index"),
                    "label": b.get("label"),
                    "n_atoms": b.get("n_atoms"),
                    "atom_range": (b.get("start", 0), b.get("stop", 0)),
                    "region_tag": b.get("region_tag"),
                }
                for b in self._load_blocks
            ],
            "current_structure_index": self._current_structure_index,
            "styles": {
                "current": None if current_style is None else current_style.info(),
                "registered_count": self.styles.count(skip_digestion=True),
                "builtin_count": len(self.styles.builtin_tags(skip_digestion=True)),
            },
            "regions": {
                "count": len(region_tags),
                "tags": region_tags,
            },
            "layers": {
                "count": len(layer_tags),
                "tags": layer_tags,
            },
            "shapes": {
                "count": len(shape_tags),
                "tags": shape_tags,
            },
            "annotations": {
                "count": len(annotation_tags),
                "tags": annotation_tags,
            },
            "measurements": {
                "count": len(measurement_tags),
                "tags": measurement_tags,
                "settings": self.measurements.settings(skip_digestion=True),
            },
            "selections": {
                "count": len(selection_tags),
                "tags": selection_tags,
            },
            "active_selection": {
                "is_empty": self.active_selection.is_empty(skip_digestion=True),
                "info": self.active_selection.info(skip_digestion=True),
            },
        }

    def _viewer_info_records(self) -> list[dict[str, Any]]:
        summary = self._viewer_info_summary()
        records: list[dict[str, Any]] = []

        whole = summary["whole"]
        records.append(
            {
                "section": "whole",
                "tag": "whole",
                "kind": "whole",
                "visible": whole["visible"],
                "active": True,
                "layer tag": None,
                "representation": whole["representation"],
                "preset": whole["preset"],
                "n atoms": None,
                "n members": None,
                "n picks": None,
                "details": ", ".join(f"{key}={value}" for key, value in sorted(whole["params"].items())) if whole["params"] else "",
            }
        )

        for block in summary.get("loads", []):
            records.append(
                {
                    "section": "loads",
                    "tag": block.get("label") or f"load{block.get('index', '')}",
                    "kind": "load",
                    "visible": None,
                    "active": True,
                    "layer tag": block.get("region_tag"),
                    "representation": None,
                    "preset": None,
                    "n atoms": block.get("n_atoms"),
                    "n members": None,
                    "n picks": None,
                    "details": f"atoms {block.get('atom_range', (0, 0))[0]}–{block.get('atom_range', (0, 0))[1]}",
                }
            )

        styles = summary["styles"]
        current_style = styles.get("current")
        records.append(
            {
                "section": "styles",
                "tag": "current",
                "kind": "style",
                "visible": None,
                "active": current_style is not None,
                "layer tag": None,
                "representation": None if current_style is None else current_style.get("representation"),
                "preset": None if current_style is None else (current_style.get("user_preset") or current_style.get("preset")),
                "n atoms": None,
                "n members": styles["registered_count"],
                "n picks": None,
                "details": (
                    f"builtins={styles['builtin_count']}"
                    if current_style is None
                    else ", ".join(
                        [f"builtins={styles['builtin_count']}"]
                        + [f"{key}={value}" for key, value in sorted((current_style.get("params") or {}).items())]
                    )
                ),
            }
        )

        for item in self.annotations.info(skip_digestion=True):
            records.append(
                {
                    "section": "annotations",
                    "tag": item.get("tag"),
                    "kind": item.get("kind"),
                    "visible": item.get("visible"),
                    "active": item.get("active"),
                    "layer tag": item.get("layer_tag"),
                    "representation": None,
                    "preset": None,
                    "n atoms": item.get("n_atoms"),
                    "n members": None,
                    "n picks": None,
                    "details": item.get("text"),
                }
            )

        for item in self.measurements.info():
            records.append(
                {
                    "section": "measurements",
                    "tag": item.get("tag"),
                    "kind": item.get("kind"),
                    "visible": item.get("visible"),
                    "active": item.get("active"),
                    "layer tag": item.get("layer_tag"),
                    "representation": None,
                    "preset": None,
                    "n atoms": None,
                    "n members": None,
                    "n picks": item.get("n_picks"),
                    "details": f"policy={item.get('endpoint_policy')}",
                }
            )

        for tag, region in sorted(self._regions.items()):
            records.append(
                {
                    "section": "regions",
                    "tag": tag,
                    "kind": "region",
                    "visible": not bool(getattr(region, "_hidden", False)),
                    "active": bool(getattr(region, "_active", False)),
                    "layer tag": None,
                    "representation": getattr(region, "representation", None),
                    "preset": getattr(region, "preset", None),
                    "n atoms": len(getattr(region, "atom_indices", ()) or ()),
                    "n members": None,
                    "n picks": None,
                    "details": getattr(region, "selection", None) or "",
                }
            )

        for tag, layer in sorted(self._layers.items()):
            members = getattr(layer, "members", {})
            n_shapes = sum(1 for member in members.values() if getattr(member, "kind", None) == "shape")
            n_annotations = sum(1 for member in members.values() if getattr(member, "kind", None) == "annotation")
            n_measurements = sum(1 for member in members.values() if getattr(member, "kind", None) == "measurement")
            records.append(
                {
                    "section": "layers",
                    "tag": tag,
                    "kind": getattr(layer, "kind", "layer"),
                    "visible": not bool(getattr(layer, "_hidden", False)),
                    "active": bool(getattr(layer, "_active", False)),
                    "layer tag": tag,
                    "representation": None,
                    "preset": None,
                    "n atoms": None,
                    "n members": len(members),
                    "n picks": None,
                    "details": f"shapes={n_shapes}, annotations={n_annotations}, measurements={n_measurements}",
                }
            )

        for tag, item in sorted(self._scene_objects.items()):
            if getattr(item, "kind", None) != "shape":
                continue
            records.append(
                {
                    "section": "shapes",
                    "tag": tag,
                    "kind": getattr(item, "meta", {}).get("shape_kind", "shape"),
                    "visible": not bool(getattr(item, "_hidden", False)),
                    "active": bool(getattr(item, "_active", False)),
                    "layer tag": getattr(item, "layer_tag", None),
                    "representation": None,
                    "preset": None,
                    "n atoms": None,
                    "n members": None,
                    "n picks": None,
                    "details": f"layer={getattr(item, 'layer_tag', None)}",
                }
            )

        for item in self.selections.info(skip_digestion=True):
            records.append(
                {
                    "section": "selections",
                    "tag": item.get("tag"),
                    "kind": "selection",
                    "visible": None,
                    "active": True,
                    "layer tag": None,
                    "representation": None,
                    "preset": None,
                    "n atoms": item.get("n_atoms"),
                    "n members": None,
                    "n picks": None,
                    "details": f"{item.get('source_kind')} / {item.get('element_level')}",
                }
            )

        active_selection = summary["active_selection"]
        active_info = active_selection["info"]
        records.append(
            {
                "section": "active_selection",
                "tag": "active_selection",
                "kind": active_info.get("source_kind"),
                "visible": None,
                "active": not active_selection["is_empty"],
                "layer tag": None,
                "representation": None,
                "preset": None,
                "n atoms": active_info.get("count_atoms"),
                "n members": None,
                "n picks": None,
                "details": f"{active_info.get('source_kind')} / {active_info.get('element_level')}",
            }
        )

        return records

    def _records_to_styler(self, records: list[dict[str, Any]]):
        from pandas import DataFrame as df

        return df(records).style.hide(axis='index')

    def _styler_to_dataframe(self, styler):
        data = getattr(styler, "data", None)
        if data is None:
            raise ValueError("Unable to extract DataFrame from Styler output.")
        return data

    def _convert_info_output(self, value: Any, output_type: str):
        if output_type == "styler":
            if isinstance(value, list):
                return self._records_to_styler(value)
            return value
        if output_type == "dataframe":
            if isinstance(value, list):
                return self._styler_to_dataframe(self._records_to_styler(value))
            return self._styler_to_dataframe(value)
        if output_type == "dictionary":
            if isinstance(value, list):
                return [dict(item) for item in value]
            return self._styler_to_dataframe(value).to_dict(orient="records")
        raise ValueError(f"Unsupported output_type {output_type!r}.")

    @signal(tags=["query"])
    @digest()
    def info(self,
             element='system',
             selection='all',
             syntax='MolSysMT',
             mask='all',
             source='all',
             output_type='styler',
             skip_digestion=False
            ):
        if source == "view":
            return self._convert_info_output(self._viewer_info_records(), output_type)

        kwargs = dict(
            element=element,
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
        )
        if "mask" in inspect.signature(msm.info).parameters:
            kwargs["mask"] = mask
        molsys_info = msm.info(self._molsys, **kwargs)

        if source == "molsys":
            return self._convert_info_output(molsys_info, output_type)

        if source == "all":
            return ViewerInfo(
                molsys_section=self._convert_info_output(molsys_info, output_type),
                view_section=self._convert_info_output(self._viewer_info_records(), output_type),
            )

        raise ValueError("info(source=...) only accepts 'all', 'molsys', or 'view'.")

    @signal(tags=["selection"])
    @digest()
    def select(
        self,
        selection="all",
        structure_indices="all",
        element="atom",
        mask=None,
        syntax="MolSysMT",
        skip_digestion=False,
    ):
        """Select indices from the current molecular system (MolSysMT selection language).

        Notes
        -----
        This method intentionally focuses on the common workflow: returning indices.
        """
        return msm.select(
            self._molsys,
            selection=selection,
            structure_indices=structure_indices,
            element=element,
            mask=mask,
            syntax=syntax,
            skip_digestion=True,
        )

    @signal(tags=["query"])
    @digest()
    def get(
        self,
        element="system",
        selection="all",
        structure_indices="all",
        mask=None,
        syntax="MolSysMT",
        get_missing_bonds=True,
        output_type="values",
        skip_digestion=False,
        **kwargs,
    ):
        """Retrieve attribute values from the current molecular system (MolSysMT get)."""
        return msm.get(
            self._molsys,
            element=element,
            selection=selection,
            structure_indices=structure_indices,
            mask=mask,
            syntax=syntax,
            get_missing_bonds=get_missing_bonds,
            output_type=output_type,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["convert"])
    @dep_digest("molsysmt")
    @digest()
    def convert(
        self,
        to_form="molsysmt.MolSys",
        *,
        selection="all",
        structure_indices="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ):
        """Convert this viewer to another form.

        Notes
        -----
        The initial implementation delegates conversion to the current
        molecular system stored in the view. Future target forms may support
        richer viewer-state-aware conversions when MolSysMT exposes them.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling convert().")

        return msm.convert(
            self._molsys,
            to_form=to_form,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )

    @signal(tags=["query"])
    @digest()
    def contains(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether the loaded molecular system contains the requested features."""
        return bool(
            msm.contains(
                self._molsys,
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )
        )

    @signal(tags=["query"])
    @digest()
    def is_composed_of(
        self,
        selection="all",
        syntax="MolSysMT",
        skip_digestion=False,
        **kwargs,
    ) -> bool:
        """Check whether the loaded molecular system is composed of the requested classes/counts."""
        return bool(
            msm.is_composed_of(
                self._molsys,
                selection=selection,
                syntax=syntax,
                skip_digestion=True,
                **kwargs,
            )
        )

    @signal(tags=["query"])
    @digest()
    def extract(
        self,
        selection="all",
        structure_indices="all",
        *,
        syntax="MolSysMT",
        debug_js: bool | None = None,
        skip_digestion: bool = False,
    ):
        """Return a new view built from a structural subset of this view.

        Regions, shapes, annotations, measurements, saved selections, and
        sections are migrated to the new view with atom indices remapped to
        the extracted subset.  See :func:`~tools.basic.extract.extract` for
        full details.
        """
        from ..tools.basic.extract import extract as _extract_view

        return _extract_view(
            self,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            debug_js=debug_js,
            skip_digestion=True,
        )

    @signal(tags=["edit"])
    @digest()
    def append_structures(
        self,
        from_molecular_system: Any,
        *,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
    ) -> None:
        """Append structures (frames) to the loaded system and refresh the viewer (live).

        Notes
        -----
        This method mutates the molecular system behind this view and then reloads the frontend payload.
        It aims to preserve regions, layers, visibility, and shapes.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling append_structures().")

        visible = self.visible_atom_indices
        msm.append_structures(
            self._molsys,
            from_molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            in_place=True,
            skip_digestion=True,
        )
        self.molecular_system = self._molsys
        self._rebuild_view_from_current_molsys(label=self._last_label, visible_atom_indices=visible)

    @signal(tags=["edit"])
    @digest()
    def set(
        self,
        *,
        element: str | None = None,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
        **kwargs: Any,
    ) -> None:
        """Set attribute values on the loaded system and refresh the viewer (live).

        This forwards to `molsysmt.set(...)` and then reloads the frontend payload so that changes
        become visible.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling set().")

        visible = self.visible_atom_indices
        self._set_molsys_attributes(
            element=element,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            **kwargs,
        )
        self.molecular_system = self._molsys
        self._rebuild_view_from_current_molsys(label=self._last_label, visible_atom_indices=visible)

    def _normalize_set_value(self, attribute: str, value: Any):
        if attribute != "coordinates":
            return value

        quantity = puw.standardize(value)
        if not puw.check(puw.get_unit(quantity), dimensionality={"[L]": 1}):
            raise ValueError("coordinates passed to set() must have length units")
        return quantity

    def _set_molsys_attributes(
        self,
        *,
        element: str | None,
        selection: str | Any,
        structure_indices: str | Any,
        syntax: str,
        **kwargs: Any,
    ) -> None:
        from molsysmt.attribute import attributes
        from molsysmt.basic import select, where_is_attribute
        from molsysmt.form import _dict_modules

        element_indices: dict[str, Any] = {}

        for attribute, raw_value in kwargs.items():
            target_element = element if element is not None else attributes[attribute]["set_to"]

            dict_indices: dict[str, Any] = {}
            if target_element != "system":
                if target_element not in element_indices:
                    if is_all(selection):
                        element_indices[target_element] = "all"
                    else:
                        element_indices[target_element] = select(
                            self._molsys,
                            element=target_element,
                            selection=selection,
                            syntax=syntax,
                            skip_digestion=True,
                        )
                dict_indices["indices"] = element_indices[target_element]

            if attributes[attribute]["runs_on_structures"]:
                dict_indices["structure_indices"] = structure_indices

            item, form = where_is_attribute(
                self._molsys,
                attribute,
                include_none=True,
                skip_digestion=True,
            )
            if item is None or form is None:
                raise ValueError(f"Attribute {attribute!r} is not available in the loaded molecular system.")

            setter_name = f"set_{attribute}_to_{target_element}"
            setter = getattr(_dict_modules[form], setter_name, None)
            if setter is None:
                raise ValueError(
                    f"Attribute {attribute!r} cannot currently be set at element level {target_element!r}."
                )

            value = self._normalize_set_value(attribute, raw_value)
            setter(item, value=value, skip_digestion=True, **dict_indices)

    @signal(tags=["edit"])
    @digest()
    def add(
        self,
        from_molecular_system: Any,
        *,
        selection: str | Any = "all",
        structure_indices: str | Any = "all",
        keep_ids: bool = True,
        syntax: str = "MolSysMT",
        label: str | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Add atoms/structures from another system into this view and refresh the viewer (live)."""
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling add().")
        if not self._load_blocks:
            self._collapse_load_blocks_to_current_whole()

        added_molsys = msm.convert(
            from_molecular_system,
            to_form="molsysmt.MolSys",
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
        )
        added_n_atoms = added_molsys.get_n_atoms()
        visible = self.visible_atom_indices
        msm.add(
            self._molsys,
            added_molsys,
            selection="all",
            structure_indices="all",
            keep_ids=keep_ids,
            in_place=True,
            syntax=syntax,
            skip_digestion=True,
        )
        self.molecular_system = self._molsys
        self._append_load_block(n_atoms=added_n_atoms, label=label)
        self._last_label = label
        self._rebuild_view_from_current_molsys(label=self._last_label, visible_atom_indices=visible)

    @signal(tags=["edit"])
    @digest()
    def remove(
        self,
        *,
        selection: str | Any | None = None,
        structure_indices: str | Any | None = None,
        syntax: str = "MolSysMT",
        skip_digestion: bool = False,
    ) -> None:
        """Remove atoms and/or structures from this view and refresh the viewer (live).

        Atom removals require remapping stored atom indices so that regions and shapes remain consistent.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling remove().")

        visible_old = self.visible_atom_indices or []
        atom_index_map: dict[int, int] | None = None

        if selection is not None:
            removed = set(msm.select(self._molsys, selection=selection, syntax=syntax, skip_digestion=True))
            n_atoms = int(msm.get(self._molsys, element="system", n_atoms=True, skip_digestion=True))
            kept = [i for i in range(n_atoms) if i not in removed]
            atom_index_map = {old: new for new, old in enumerate(kept)}

        self._molsys = msm.remove(
            self._molsys,
            selection=selection,
            structure_indices=structure_indices,
            to_form="molsysmt.MolSys",
            syntax=syntax,
            skip_digestion=True,
        )
        self.molecular_system = self._molsys
        self._collapse_load_blocks_to_current_whole()

        self._rebuild_view_from_current_molsys(
            label=self._last_label,
            atom_index_map=atom_index_map,
            visible_atom_indices=visible_old,
        )

    # --- Export helpers for docs/notebooks ---

    def _write_html_impl(
        self,
        output_filename: str,
        *,
        title: str = "MolSysViewer",
        include_controls: bool = True,
        include_popout: bool = True,
        mode: str = "standalone",
        inline_messages: bool = True,
        runtime_urls: Sequence[str] | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export this viewer widget to an HTML file.

        Parameters
        ----------
        output_filename:
            Path to the HTML file to create.
        title:
            Optional title for the exported HTML page.
        include_controls:
            If ``True`` (default), include the on-canvas control buttons
            (Reset, Fullscreen, background toggle, Spin, Swing) in the exported view.
            Set this to ``False`` if you prefer a minimal viewer without these controls,
            for example when embedding inside another application that already provides
            its own UI.
        include_popout:
            If ``True`` (default), include the popout button and allow opening a popout window.
        mode:
            - ``"standalone"`` (default): produce a self-contained HTML using the widget embed machinery.
            - ``"lite"``: produce a lightweight HTML that loads the runtime from the CDN
              and replays messages (suitable for embedded docs-light views).
        inline_messages:
            Only used when ``mode="lite"``. If ``True`` (default), embed the replay messages inline in the HTML.
        """
        if mode not in {"standalone", "lite"}:
            raise ValueError("view.export.html(mode=...) must be 'standalone' or 'lite'.")

        # If the frontend is live, request a fresh camera snapshot so exports
        # reflect the latest user view (best-effort, no hard dependency).
        self._request_camera_snapshot()

        messages = self._build_export_messages()

        if mode == "standalone":
            # Serialize the message history so the exported HTML can replay all
            # actions (loads/shapes/visibility) without needing a live Python kernel.
            self.widget.initial_messages = messages
            html = self._build_standalone_html(
                title=title,
                include_controls=include_controls,
                include_popout=include_popout,
            )
        else:
            html = self._build_lite_html(
                title=title,
                include_controls=include_controls,
                include_popout=include_popout,
                messages=messages,
                inline_messages=inline_messages,
                runtime_urls=runtime_urls,
            )
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html)

    def _request_camera_snapshot(self, timeout_s: float = 0.35) -> bool:
        """Ask the frontend for a camera snapshot (best-effort)."""
        if not self._ready:
            return False
        previous = self._last_camera_snapshot
        try:
            self.widget.send({"op": "request_camera_snapshot"})
        except Exception:
            return False
        if timeout_s <= 0:
            return True
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            current = self._last_camera_snapshot
            if current is not None and current is not previous:
                return True
            time.sleep(0.01)
        return False

    def _request_image_export(
        self,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        preset: str = "current",
        camera_snapshot: dict | None = None,
        timeout_s: float = 2.0,
    ) -> dict | None:
        """Ask the frontend for an image export (best-effort)."""
        if not self._ready:
            return None
        previous = self._last_image_export_event
        payload: dict[str, Any] = {
            "op": "request_image_export",
            "transparent": bool(transparent),
            "scale": float(scale),
            "preset": str(preset),
        }
        if width_px is not None:
            payload["width"] = int(width_px)
        if height_px is not None:
            payload["height"] = int(height_px)
        if camera_snapshot:
            payload["camera_snapshot"] = dict(camera_snapshot)
        try:
            self.widget.send(payload)
        except Exception:
            return None
        if timeout_s <= 0:
            return self._last_image_export_event
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            current = self._last_image_export_event
            if current is not None and current is not previous:
                return dict(current)
            time.sleep(0.01)
        return None

    def _export_image_headless(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        timeout_s: float = 15.0,
    ) -> None:
        """Render the scene without a live Jupyter frontend and save a PNG.

        Tries rendering backends in priority order:

        1. **Qt WebEngine** (``PySide6_uibcdf`` or ``PySide6``) — zero extra setup on
           Linux standalone installations where the package is already bundled.
        2. **playwright** — true headless rendering for all other environments;
           requires ``playwright install chromium`` once (shared with e2e tests).

        Called automatically by ``_export_image_impl`` when the Jupyter frontend is
        not ready.
        """
        errors: list[str] = []

        # --- Backend 1: Qt WebEngine (preferred on Linux standalone) ---
        try:
            self._export_image_headless_qt(
                output_filename,
                width_px=width_px,
                height_px=height_px,
                scale=scale,
                transparent=transparent,
                timeout_s=timeout_s,
            )
            return
        except ImportError as exc:
            errors.append(f"Qt backend unavailable: {exc}")
        except Exception as exc:
            errors.append(f"Qt backend failed: {exc}")

        # --- Backend 2: playwright ---
        try:
            self._export_image_headless_playwright(
                output_filename,
                width_px=width_px,
                height_px=height_px,
                scale=scale,
                transparent=transparent,
                timeout_s=timeout_s,
            )
            return
        except ImportError as exc:
            errors.append(f"playwright backend unavailable: {exc}")
        except Exception as exc:
            errors.append(f"playwright backend failed: {exc}")

        raise RuntimeError(
            "Headless image export failed — no rendering backend is available.\n"
            + "\n".join(f"  • {e}" for e in errors)
            + "\n\nTo enable headless export, install playwright and its browser:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )

    def _export_image_headless_qt(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        timeout_s: float = 15.0,
    ) -> None:
        """Headless render via Qt WebEngine (PySide6_uibcdf or PySide6)."""
        import os
        import pathlib
        import sys
        import tempfile

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        # Enable SwiftShader software WebGL so Mol* renders without a GPU.
        os.environ.setdefault(
            "QTWEBENGINE_CHROMIUM_FLAGS",
            "--use-gl=swiftshader --disable-gpu",
        )

        # Try UIBCDF standalone package first, then standard PySide6.
        QApplication = QWebEngineView = QUrl = QTimer = QEventLoop = None
        for _pkg in ("PySide6_uibcdf", "PySide6"):
            try:
                _w = __import__(f"{_pkg}.QtWidgets", fromlist=["QApplication"])
                _e = __import__(f"{_pkg}.QtWebEngineWidgets", fromlist=["QWebEngineView"])
                _c = __import__(f"{_pkg}.QtCore", fromlist=["QUrl", "QTimer", "QEventLoop"])
                QApplication = _w.QApplication
                QWebEngineView = _e.QWebEngineView
                QUrl = _c.QUrl
                QTimer = _c.QTimer
                QEventLoop = _c.QEventLoop
                break
            except ImportError:
                continue

        if QApplication is None:
            raise ImportError(
                "Neither PySide6_uibcdf nor PySide6 with QtWebEngineWidgets is available."
            )

        viewer_js = pathlib.Path(__file__).parent.parent / "viewer.js"
        if not viewer_js.exists():
            raise RuntimeError(f"Cannot find bundled viewer.js at {viewer_js}")

        messages = self._build_export_messages()
        html = self._build_lite_html(
            title="MolSysViewer Headless Export",
            include_controls=False,
            include_popout=False,
            messages=messages,
            inline_messages=True,
            # Qt WebEngine can load file:// imports from the same local origin.
            runtime_urls=[viewer_js.resolve().as_uri()],
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8"
        ) as _f:
            _f.write(html)
            tmp_html = _f.name

        try:
            w = int(width_px or 1280)
            h = int(height_px or 720)

            app = QApplication.instance() or QApplication(sys.argv)  # type: ignore[misc]

            loop = QEventLoop()
            view = QWebEngineView()
            view.resize(w, h)
            view.show()

            state: dict[str, Any] = {"done": False, "error": None}

            def _check_rendered() -> None:
                def _cb(result: Any) -> None:
                    if result:
                        state["done"] = True
                        loop.quit()
                    else:
                        QTimer.singleShot(200, _check_rendered)
                view.page().runJavaScript(  # type: ignore[union-attr]
                    "!!document.getElementById('molsysviewer-root')"
                    "?.getAttribute('data-molsysviewer-rendered')",
                    _cb,
                )

            def _on_load(ok: bool) -> None:
                if not ok:
                    state["error"] = "Qt WebEngine failed to load the page."
                    loop.quit()
                    return
                QTimer.singleShot(300, _check_rendered)

            def _on_timeout() -> None:
                if not state["done"]:
                    state["error"] = "Timeout waiting for viewer to render (Qt backend)."
                    loop.quit()

            view.loadFinished.connect(_on_load)  # type: ignore[attr-defined]
            view.setUrl(QUrl.fromLocalFile(tmp_html))  # type: ignore[union-attr]
            QTimer.singleShot(int(timeout_s * 1000), _on_timeout)
            loop.exec()

            if state["error"]:
                raise RuntimeError(state["error"])

            pixmap = view.grab()
            pixmap.save(output_filename, "PNG")
        finally:
            try:
                os.unlink(tmp_html)
            except OSError:
                pass

    def _export_image_headless_playwright(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        timeout_s: float = 15.0,
    ) -> None:
        """Headless render via playwright (shared Chromium browser binary)."""
        import http.server
        import os
        import pathlib
        import socket
        import tempfile
        import threading

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "playwright is not installed. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        viewer_js_path = pathlib.Path(__file__).parent.parent / "viewer.js"
        if not viewer_js_path.exists():
            raise RuntimeError(f"Cannot find bundled viewer.js at {viewer_js_path}")
        pkg_dir = str(viewer_js_path.parent)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as _s:
            _s.bind(("localhost", 0))
            port = _s.getsockname()[1]

        messages = self._build_export_messages()
        html = self._build_lite_html(
            title="MolSysViewer Headless Export",
            include_controls=False,
            include_popout=False,
            messages=messages,
            inline_messages=True,
            runtime_urls=[f"http://localhost:{port}/viewer.js"],
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", dir=pkg_dir, delete=False, encoding="utf-8"
        ) as _f:
            _f.write(html)
            html_name = os.path.basename(_f.name)
            html_abs = _f.name

        _pkg_dir_ref = pkg_dir

        class _SilentHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, directory=_pkg_dir_ref, **kwargs)

            def log_message(self, *args: Any) -> None:
                pass

        httpd = http.server.HTTPServer(("localhost", port), _SilentHandler)
        threading.Thread(
            target=httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        ).start()

        try:
            w = int(width_px or 1280)
            h = int(height_px or 720)
            dpr = max(0.1, float(scale))
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                ctx = browser.new_context(
                    viewport={"width": w, "height": h},
                    device_scale_factor=dpr,
                )
                page = ctx.new_page()
                page.goto(
                    f"http://localhost:{port}/{html_name}",
                    timeout=int(timeout_s * 1000),
                )
                page.wait_for_selector(
                    "[data-molsysviewer-rendered]",
                    timeout=int(timeout_s * 1000),
                )
                page.screenshot(
                    path=output_filename,
                    full_page=False,
                    omit_background=bool(transparent),
                )
                browser.close()
        finally:
            httpd.shutdown()
            try:
                os.unlink(html_abs)
            except OSError:
                pass

    def _export_image_impl(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 1.0,
        transparent: bool = False,
        preset: str = "current",
        camera_snapshot: dict | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export the current viewer scene as a PNG image file."""
        event = self._request_image_export(
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            transparent=transparent,
            preset=preset,
            camera_snapshot=camera_snapshot,
        )
        if not event:
            # No live frontend — fall back to headless playwright rendering
            self._export_image_headless(
                output_filename,
                width_px=width_px,
                height_px=height_px,
                scale=scale,
                transparent=transparent,
            )
            return

        data_uri = event.get("data_uri")
        if not isinstance(data_uri, str) or not data_uri.startswith("data:image/png;base64,"):
            raise RuntimeError("Frontend image export did not return a PNG data URI.")

        image_bytes = base64.b64decode(data_uri.split(",", 1)[1])
        with open(output_filename, "wb") as f:
            f.write(image_bytes)

    def _export_figure_impl(
        self,
        output_filename: str,
        *,
        width_px: int | None = None,
        height_px: int | None = None,
        scale: float = 2.0,
        background: str = "white",
        preset: str = "publication-light",
        camera_snapshot: dict | None = None,
        skip_digestion: bool = False,
    ) -> None:
        """Export a first figure-oriented PNG by mapping figure defaults onto image export."""
        normalized_background = str(background).strip().lower()
        normalized_preset = str(preset).strip() or "publication-light"

        if normalized_background == "transparent":
            transparent = True
            export_preset = "current"
        elif normalized_background == "dark":
            transparent = False
            export_preset = "publication-dark" if normalized_preset == "publication-light" else normalized_preset
        elif normalized_background == "current":
            transparent = False
            export_preset = normalized_preset if normalized_preset != "publication-light" else "current"
        else:
            transparent = False
            export_preset = "publication-light" if normalized_preset == "publication-light" else normalized_preset

        self._export_image_impl(
            output_filename,
            width_px=width_px,
            height_px=height_px,
            scale=scale,
            transparent=transparent,
            preset=export_preset,
            camera_snapshot=camera_snapshot,
            skip_digestion=True,
        )

    def _load_anywidget_bundle(self) -> str:
        """Return the JS bundle for anywidget if available to inline in exports."""
        try:
            import anywidget  # type: ignore
        except Exception:
            return ""

        from pathlib import Path

        locations = [
            Path(anywidget.__file__).parent / "nbextension" / "index.js",
            Path(anywidget.__file__).parent / "labextension" / "index.js",
        ]

        sources: list[str] = []
        for path in locations:
            if path.exists():
                try:
                    src = path.read_text(encoding="utf-8")
                    # If this bundle ends with an anonymous AMD define, give it a name
                    # so requirejs can register it when inlined.
                    src = src.replace(
                        'define(["@jupyter-widgets/base"], widget_default);',
                        'define("anywidget-inline", ["@jupyter-widgets/base"], widget_default);\n'
                        'define("anywidget", ["anywidget-inline"], function(m){return m;});',
                    )
                    sources.append(src)
                except Exception:
                    continue

        return "\n".join(sources)

    def _build_standalone_html(
        self,
        title: str,
        include_controls: bool = True,
        include_popout: bool = True,
    ) -> str:
        """Create a minimal standalone HTML embedding only this widget."""
        # Ensure initial_messages is in sync before exporting
        self.widget.initial_messages = self._build_export_messages()

        layout_state = self.widget.layout.get_state(drop_defaults=False)
        widget_state = self.widget.get_state(drop_defaults=False)
        # Override toolbar visibility for the exported HTML without mutating
        # the live widget trait in notebooks.
        widget_state["show_controls"] = bool(include_controls)
        widget_state["layout"] = f"IPY_MODEL_{self.widget.layout.model_id}"
        # Avoid duplicating the full viewer bundle in exports: the widget already
        # carries its ESM source under `_esm`. The popout can fall back to `_esm`
        # when `popup_js_source` is empty.
        if "popup_js_source" in widget_state:
            widget_state["popup_js_source"] = ""
        widget_state["enable_popout"] = bool(include_popout)

        state_json = {
            "version_major": 2,
            "version_minor": 0,
            "state": {
                self.widget.layout.model_id: {
                    "model_name": "LayoutModel",
                    "model_module": "@jupyter-widgets/base",
                    "model_module_version": _WIDGETS_BASE_VERSION,
                    "state": layout_state,
                },
                self.widget.model_id: {
                    "model_name": self.widget._model_name,  # type: ignore[attr-defined]
                    "model_module": self.widget._model_module,  # type: ignore[attr-defined]
                    "model_module_version": self.widget._model_module_version,  # type: ignore[attr-defined]
                    "state": widget_state,
                },
            },
        }
        view_spec = {
            "version_major": 2,
            "version_minor": 0,
            "model_id": self.widget.model_id,
        }

        inline_anywidget = self._load_anywidget_bundle()
        anywidget_script = ""
        if inline_anywidget:
            anywidget_script = (
                "<script>\n"
                "requirejs.config({\n"
                "  map: {'*': {'anywidget': 'anywidget-inline'}},\n"
                f"  paths: {{'@jupyter-widgets/base': 'https://cdn.jsdelivr.net/npm/@jupyter-widgets/base@{_WIDGETS_BASE_VERSION}/dist/index'}}\n"
                "});\n"
                "</script>\n"
                f"<script>\n{inline_anywidget}\n</script>\n"
            )

        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
</head>
<body>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js" crossorigin="anonymous"></script>
<script src="https://cdn.jsdelivr.net/npm/@jupyter-widgets/html-manager@{_HTML_MANAGER_VERSION}/dist/embed-amd.js" crossorigin="anonymous"></script>
{anywidget_script}
<script type="application/vnd.jupyter.widget-state+json">
{json.dumps(state_json, separators=(',', ':'))}
</script>
<script type="application/vnd.jupyter.widget-view+json">
{json.dumps(view_spec, separators=(',', ':'))}
</script>

</body>
</html>
"""
        return template

    def _build_lite_html(
        self,
        *,
        title: str,
        include_controls: bool,
        include_popout: bool,
        messages: list[dict],
        inline_messages: bool,
        runtime_urls: Sequence[str] | None = None,
    ) -> str:
        """Create a lightweight HTML that loads a shared runtime and replays messages."""
        # This HTML is meant to be embedded and load the runtime from the CDN
        # (jsDelivr). Keep it independent from the widget manager to avoid
        # bundling megabytes per example.
        from .._version import __version__ as _pkg_version
        base_version = _pkg_version.split("+", 1)[0]
        runtime_cdn = f"https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@{base_version}/dist/viewer.js"

        ui_config = {
            "show_controls": bool(include_controls),
            "autohide_controls": bool(getattr(self.widget, "autohide_controls", False)),
            "controls_position": list(getattr(self.widget, "controls_position", ["top", "right"])),
            "controls_position_fullscreen": list(getattr(self.widget, "controls_position_fullscreen", ["bottom", "right"])),
            "controls_mode": str(getattr(self.widget, "controls_mode", "classic")),
            "panel_mode_style": str(getattr(self.widget, "panel_mode_style", "drawer")),
            "enable_popout": bool(include_popout),
            "debug_js": bool(getattr(self.widget, "debug_js", False)),
        }

        messages_json = self._json_for_html_script(messages) if inline_messages else "[]"
        ui_json = self._json_for_html_script(ui_config)

        runtime_candidates = list(runtime_urls or [runtime_cdn])
        runtime_candidates_json = self._json_for_html_script(runtime_candidates)

        template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
    #molsysviewer-root {{ width: 100%; height: 100%; min-height: 400px; position: relative; }}
  </style>
</head>
<body>
  <div id="molsysviewer-root"></div>
  <script id="molsysviewer-ui" type="application/json">{ui_json}</script>
  <script id="molsysviewer-messages" type="application/json">{messages_json}</script>
  <script id="molsysviewer-runtime-candidates" type="application/json">{runtime_candidates_json}</script>
  <script type="module">
    const el = document.getElementById("molsysviewer-root");
    const ui = JSON.parse(document.getElementById("molsysviewer-ui").textContent || "{{}}");
    const messages = JSON.parse(document.getElementById("molsysviewer-messages").textContent || "[]");
    const candidates = JSON.parse(document.getElementById("molsysviewer-runtime-candidates").textContent || "[]");

    let lastError = null;
    for (const rel of candidates) {{
      try {{
        const moduleUrl = new URL(rel, window.location.href).href;
        const mod = await import(moduleUrl);
        const boot = mod.bootDocsView || mod.boot_docs_view || mod.default?.bootDocsView;
        if (typeof boot !== "function") {{
          throw new Error("bootDocsView not found in runtime: " + moduleUrl);
        }}
        await boot({{
          el,
          initialMessages: messages,
          ui,
          runtimeUrl: moduleUrl,
        }});
        // Allow Mol* to finish rendering all queued frames before signalling
        // headless screenshot tools (e.g. playwright) that the scene is ready.
        await new Promise(resolve => setTimeout(resolve, 2000));
        el.setAttribute("data-molsysviewer-rendered", "true");
        lastError = null;
        break;
      }} catch (e) {{
        lastError = e;
      }}
    }}
    if (lastError) {{
      console.error("[MolSysViewer docs] Failed to load runtime.", lastError);
      el.textContent = "MolSysViewer failed to load. See console for details.";
    }}
  </script>
</body>
</html>
"""
        return template

# Preserve the historical public module identity for decorated methods.
# Several argument-digestion rules key off `molsysviewer.viewer...` caller paths.
MolSysView.__module__ = "molsysviewer.viewer"
for _name, _value in MolSysView.__dict__.items():
    if callable(_value) and getattr(_value, "__module__", None) == __name__:
        try:
            _value.__module__ = "molsysviewer.viewer"
        except Exception:
            pass
