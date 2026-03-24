from __future__ import annotations

from typing import Any, Dict, Mapping
import base64
import time
import inspect
import json
import re

import molsysmt as msm
import numpy as np
from smonitor import signal
from smonitor.integrations import emit_from_catalog
from depdigest import dep_digest

from ._pyunitwizard import puw
from ._private.arg_digestion import digest
from ._private.smonitor import CATALOG, PACKAGE_ROOT, META
from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .loaders import load_from_molsysmt as _load_from_molsysmt
from .annotations import AnnotationsManager
from .active_selection import ActiveSelection
from .addons import ViewAddonsManager, addons as global_addons
from .exports import ExportManager
from .interaction_targets import InteractionTarget
from .measurements import MeasurementsManager
from .selections import SelectionsManager, Selection
from .styles import StylesManager
from .shapes import ShapesManager
from .regions import Region
from .whole import Whole
from .layers import Layer
from . import config
from .config.user_presets import user_presets

_HTML_MANAGER_VERSION = "1.0.1"
_WIDGETS_BASE_VERSION = "2.0.0"

_REPR_ALIASES = {
    "sticks": "ball-and-stick",
    "ball_and_stick": "ball-and-stick",
    "ballstick": "ball-and-stick",
    "licorice": "line",
    "lines": "line",
    "wire": "line",
    "wireframe": "line",
    "ribbon": "backbone",
    "surface": "molecular-surface",
    "vdw": "spacefill",
}

_ALLOWED_REPRS = {
    "cartoon",
    "backbone",
    "ball-and-stick",
    "carbohydrate",
    "ellipsoid",
    "gaussian-surface",
    "gaussian-volume",
    "label",
    "line",
    "molecular-surface",
    "orientation",
    "plane",
    "point",
    "putty",
    "spacefill",
}

_PRESET_ALIASES = {
    "automatic": "auto",
}

_ALLOWED_PRESETS = {
    "auto",
    "atomic-detail",
    "polymer-and-ligand",
    "polymer-cartoon",
    "coarse-surface",
    "empty",
}


def _signal_value(args: tuple[Any, ...], kwargs: dict[str, Any], index: int, name: str) -> Any:
    if name in kwargs:
        return kwargs[name]
    if len(args) > index:
        return args[index]
    return None


def _load_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    molecular_system = _signal_value(args, kwargs, 1, "molecular_system")
    return {"molecular_system": type(molecular_system).__name__ if molecular_system is not None else None}


def _zoom_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {"selection": _signal_value(args, kwargs, 1, "selection")}


def _controls_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "visible": _signal_value(args, kwargs, 1, "visible"),
        "autohide": _signal_value(args, kwargs, 2, "autohide"),
    }


def _camera_snapshot_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    snapshot = _signal_value(args, kwargs, 1, "snapshot")
    return {
        "duration_ms": _signal_value(args, kwargs, 2, "duration_ms"),
        "snapshot_keys": sorted(snapshot.keys()) if isinstance(snapshot, dict) else [],
    }


def _write_html_signal_extra(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "output_filename": _signal_value(args, kwargs, 1, "output_filename"),
        "mode": _signal_value(args, kwargs, 5, "mode"),
        "include_popout": _signal_value(args, kwargs, 4, "include_popout"),
    }


def _quantity_value_in_unit(value: Any, unit_name: str) -> float:
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    if puw.is_unit(value):
        value = puw.quantity(1.0, value)
    return float(puw.get_value(value, to_unit=unit_name))


class MolSysView:
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
        self._last_image_export_event: dict | None = None
        self._last_hover_event: dict | None = None
        self._last_click_event: dict | None = None
        self._last_context_event: dict | None = None
        self._last_context_action_event: dict | None = None
        self._last_active_selection_event: dict | None = None
        self._last_tool_state_event: dict | None = None
        self._last_measurement_created_event: dict | None = None
        self._last_panel_mode_state_event: dict | None = None
        self._shape_history: list[dict] = []
        self._annotation_history: list[dict] = []
        self._measurement_history: list[dict] = []
        self._selection_history: list[dict] = []
        self._last_label: str | None = None

        self._regions: Dict[str, Region] = {}
        self._layers: Dict[str, Layer] = {}
        self._selections: Dict[str, Selection] = {}
        self._region_counter = 0
        self._layer_counter = 0
        self._global_hidden = False

        self.whole = Whole(self)
        self.styles = StylesManager(self)
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
            if tag and tag not in self._layers:
                layer = Layer(self, tag, kind=content.get("kind"), meta=content.get("meta") or {})
                self._layers[tag] = layer
            elif tag and tag in self._layers:
                layer = self._layers[tag]
                layer.kind = content.get("kind", layer.kind)
                if content.get("meta"):
                    layer.meta.update(content.get("meta"))
        elif event == "layer_deleted":
            tag = content.get("tag")
            if tag:
                self._unregister_layer(tag)
        elif event == "registry_cleared":
            self._regions.clear()
            self._layers.clear()
            self._region_counter = 0
            self._layer_counter = 0
            self._global_hidden = False
            self.whole = Whole(self)
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
        elif event == "interaction_hover":
            self._last_hover_event = dict(content)
        elif event == "interaction_click":
            self._last_click_event = dict(content)
        elif event == "interaction_context_menu":
            self._last_context_event = dict(content)
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
                return
            if action == "create_region_from_selection":
                self.new_region_from_active_selection(skip_digestion=True)
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
                self.annotations.add_label_from_active_selection(text=text.strip(), skip_digestion=True)
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
            elif action == "persist_last_measurement":
                self.measurements.persist_last_measurement(skip_digestion=True)
        elif event == "interaction_active_selection_changed":
            self._last_active_selection_event = dict(content)
        elif event == "interaction_tool_state":
            self._last_tool_state_event = dict(content)
        elif event == "interaction_measurement_created":
            self._last_measurement_created_event = dict(content)
        elif event == "panel_mode_state":
            self._last_panel_mode_state_event = dict(content)
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

    def _next_layer_tag(self) -> str:
        self._layer_counter += 1
        return f"layer{self._layer_counter}"

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
        if value is None:
            return None
        key = value.replace("_", "-").lower().strip()
        key = _REPR_ALIASES.get(key, key)
        if key not in _ALLOWED_REPRS:
            raise ValueError(f"Unsupported representation type '{value}'. Allowed: {sorted(_ALLOWED_REPRS)}")
        return key

    def _normalize_representation_preset(self, value: str | None) -> str | None:
        if value is None:
            return None
        key = value.replace("_", "-").lower().strip()
        key = _PRESET_ALIASES.get(key, key)
        if key in _ALLOWED_PRESETS:
            return key
        if key in user_presets:
            return key
        raise ValueError(f"Unsupported preset '{value}'. Allowed: {sorted(_ALLOWED_PRESETS)} + user presets {list(user_presets)}")

    def _unregister_region(self, tag: str) -> None:
        self._regions.pop(tag, None)

    def _unregister_layer(self, tag: str) -> None:
        self._layers.pop(tag, None)

    def _reregister_layer(self, old_tag: str, new_tag: str, layer: Layer) -> None:
        if old_tag in self._layers:
            self._layers.pop(old_tag, None)
        self._layers[new_tag] = layer

    def _resolve_user_preset(self, preset: str | None):
        if preset is None:
            return None
        key = preset.replace("_", "-").lower().strip()
        cfg = user_presets.get(key)
        if cfg is None:
            return None
        if self._molsys is None:
            raise ValueError("User presets require a loaded molecular system to resolve selections.")
        rules = []
        for rule in cfg.get("rules", []) or []:
            if not isinstance(rule, dict):
                continue
            new_rule = dict(rule)
            if "atom_indices" not in new_rule:
                sel = new_rule.get("selection")
                if sel is not None:
                    try:
                        from ._private.arg_digestion import digest_selection_and_syntax

                        sel, syntax = digest_selection_and_syntax(
                            sel,
                            syntax="MolSysMT",
                            caller="molsysviewer.viewer.MolSysView._resolve_user_preset",
                        )
                        new_rule["atom_indices"] = list(
                            msm.select(self._molsys, selection=sel, syntax=syntax, skip_digestion=True)
                        )
                    except Exception:
                        raise ValueError(f"Unable to resolve selection '{sel}' for user preset '{preset}'")
            rules.append(new_rule)
        return {
            "name": key,
            "base": cfg.get("base"),
            "options": cfg.get("options") or {},
            "rules": rules,
        }

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

    @signal(tags=["viewer", "panel"])
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

    @signal(tags=["viewer", "panel"])
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

    @signal(tags=["viewer", "panel"])
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

    @signal(tags=["viewer", "panel", "query"])
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

    @signal(tags=["viewer", "panel", "query"])
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

    # --- util interno ---

    def _tag_from_message(self, msg: dict) -> str | None:
        tag = msg.get("tag")
        if isinstance(tag, str) and tag:
            return tag
        options = msg.get("options")
        if isinstance(options, dict):
            opt_tag = options.get("tag")
            if isinstance(opt_tag, str) and opt_tag:
                return opt_tag
        return None

    def _record_shape_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            if not isinstance(cleared_tag, str):
                return
            self._shape_history = [
                m for m in self._shape_history if self._tag_from_message(m) != cleared_tag
            ]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
                return
            rewritten: list[dict] = []
            for item in self._shape_history:
                tag = self._tag_from_message(item)
                if tag != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options["tag"] = new_tag
                    updated["options"] = options
                rewritten.append(updated)
            self._shape_history = rewritten
            return

        if op == "clear_shapes_by_tag":
            cleared_tag = msg.get("tag")
            if cleared_tag is None:
                self._shape_history.clear()
                return
            if not isinstance(cleared_tag, str):
                return
            self._shape_history = [
                m for m in self._shape_history if self._tag_from_message(m) != cleared_tag
            ]
            return

        if op in {"add_label", "add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return

        if not op.startswith("add_"):
            return

        self._shape_history.append(dict(msg))

    def _record_annotation_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "clear_scene":
            options = msg.get("options")
            if isinstance(options, dict) and bool(options.get("labels")):
                self._annotation_history.clear()
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            if not isinstance(cleared_tag, str):
                return
            self._annotation_history = [
                m for m in self._annotation_history if self._tag_from_message(m) != cleared_tag
            ]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
                return
            rewritten: list[dict] = []
            for item in self._annotation_history:
                tag = self._tag_from_message(item)
                if tag != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options["tag"] = new_tag
                    updated["options"] = options
                rewritten.append(updated)
            self._annotation_history = rewritten
            return

        if op == "update_label":
            updated_tag = self._tag_from_message(msg)
            if updated_tag is None:
                return
            rewritten: list[dict] = []
            for item in self._annotation_history:
                if self._tag_from_message(item) != updated_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                else:
                    options = {}
                new_options = msg.get("options")
                if isinstance(new_options, dict):
                    if "text" in new_options:
                        options["text"] = new_options["text"]
                    if "atom_indices" in new_options:
                        options["atom_indices"] = new_options["atom_indices"]
                    if "tag" in new_options:
                        options["tag"] = new_options["tag"]
                updated["options"] = options
                rewritten.append(updated)
            self._annotation_history = rewritten
            return

        if op != "add_label":
            return

        self._annotation_history.append(dict(msg))

    def _record_measurement_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "delete_layer":
            cleared_tag = msg.get("tag")
            if not isinstance(cleared_tag, str):
                return
            self._measurement_history = [
                m for m in self._measurement_history if self._tag_from_message(m) != cleared_tag
            ]
            return

        if op == "set_layer_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
                return
            rewritten: list[dict] = []
            for item in self._measurement_history:
                tag = self._tag_from_message(item)
                if tag != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                options = updated.get("options")
                if isinstance(options, dict):
                    options = dict(options)
                    options["tag"] = new_tag
                    updated["options"] = options
                rewritten.append(updated)
            self._measurement_history = rewritten
            return

        if op not in {"add_distance_measurement", "add_angle_measurement", "add_dihedral_measurement"}:
            return

        self._measurement_history.append(dict(msg))

    def _record_selection_message(self, msg: dict) -> None:
        op = msg.get("op")
        if not isinstance(op, str):
            return

        if op == "clear_selections":
            self._selection_history.clear()
            return

        if op == "delete_selection":
            cleared_tag = msg.get("tag")
            if not isinstance(cleared_tag, str):
                return
            self._selection_history = [m for m in self._selection_history if m.get("tag") != cleared_tag]
            return

        if op == "set_selection_tag":
            old_tag = msg.get("tag")
            new_tag = msg.get("new_tag")
            if not isinstance(old_tag, str) or not isinstance(new_tag, str):
                return
            rewritten: list[dict] = []
            for item in self._selection_history:
                if item.get("tag") != old_tag:
                    rewritten.append(item)
                    continue
                updated = dict(item)
                updated["tag"] = new_tag
                rewritten.append(updated)
            self._selection_history = rewritten
            return

        if op != "save_selection":
            return

        self._selection_history.append(dict(msg))

    def _send(self, msg: dict) -> None:
        """Send a message to the frontend or queue it if the frontend is not ready yet."""
        self._message_history.append(msg)
        self._record_shape_message(msg)
        self._record_annotation_message(msg)
        self._record_measurement_message(msg)
        self._record_selection_message(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)

    def _send_replay(self, msg: dict) -> None:
        """Send a message while rebuilding state, without updating shape registries."""
        self._message_history.append(msg)
        if self._ready:
            self.widget.send(msg)
        else:
            self._pending_messages.append(msg)

    def _update_visibility_in_frontend(self):
        if self.atom_mask is None:
            return
        self._send({
            "op": "update_visibility",
            "options": {"visible_atom_indices": self.visible_atom_indices},
        })

    def _sync_addons_runtime(self) -> None:
        addon_names = self.addons.enabled(skip_digestion=True)
        workspace_specs = self.addons.workspace_specs(skip_digestion=True)
        panel_specs = self.addons.panel_specs(skip_digestion=True)
        workbench_sections = self.addons.workbench_section_specs(skip_digestion=True)
        context_action_specs = self.addons.context_action_specs(skip_digestion=True)
        export_helper_specs = self.addons.export_helper_specs(skip_digestion=True)
        self._send(
            {
                "op": "set_addon_runtime_summary",
                "addons": addon_names,
                "workspace_specs": workspace_specs,
                "panel_specs": panel_specs,
                "workbench_sections": workbench_sections,
                "context_action_specs": context_action_specs,
                "export_helper_specs": export_helper_specs,
            }
        )

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

        from .loaders.load_molsysmt import _serialize_molsys_payload
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

        n_atoms = int(self._molsys.topology.get_n_atoms())
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
        skip_digestion: bool = False,
    ) -> None:
        """Load a molecular system (MolSysMT-compatible) into the viewer."""
        _load_from_molsysmt(
            molecular_system=molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            label=label,
            skip_digestion=True,
            view=self,
        )
        self._last_label = label

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
        """Focus the camera on the geometric center of a selection of atoms.

        Parameters
        ----------
        selection
            MolSysMT selection string/expression or a list of atom indices. If a list
            is provided, it is passed through MolSysMT and used directly.
        structure_indices
            Structure indices to apply when resolving the selection.
        syntax
            Selection syntax understood by MolSysMT.
        duration
            Transition duration for the camera move (any time unit supported by PyUnitWizard).
        duration_ms
            Backward-compatible alias for ``duration``. If provided, it overrides ``duration``.
        extra_radius
            Extra padding (Å) added to the selection's bounding sphere.
        min_radius
            Minimum radius (Å) to enforce for the camera focus.
        """
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling zoom().")

        atom_indices = msm.select(
            self._molsys,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
        )
        if not atom_indices:
            raise ValueError("Cannot zoom: empty selection.")

        if duration_ms is not None:
            duration = duration_ms
        duration_ms_value = _quantity_value_in_unit(duration, "ms")
        extra_radius = round(_quantity_value_in_unit(extra_radius, "angstroms"), 6)
        min_radius = round(_quantity_value_in_unit(min_radius, "angstroms"), 6)

        self._send(
            {
                "op": "zoom",
                "atom_indices": atom_indices,
                "options": {
                    "duration_ms": int(duration_ms_value),
                    "extra_radius": float(extra_radius),
                    "min_radius": float(min_radius),
                },
            }
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
        """Focus the camera on a selection of atoms."""
        self.zoom(
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
        """Focus the camera on a region identified by tag or region object."""
        if isinstance(region, str):
            target = self._regions.get(region)
            if target is None:
                raise KeyError(f"Unknown region tag: {region!r}")
        elif isinstance(region, Region):
            target = region
        else:
            raise TypeError("region must be a region tag or Region instance.")

        selection: Any
        syntax = "MolSysMT"
        if target.atom_indices is not None:
            selection = list(target.atom_indices)
        else:
            selection = target.selection
            syntax = "MolSysMT"

        self.focus_selection(
            selection=selection,
            syntax=syntax,
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
                tag for tag, layer in self._layers.items() if getattr(layer, "kind", None) == "annotation"
            ]
            for tag in annotation_tags:
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
        """Reset the camera / view in the frontend."""
        self._send({
            "op": "reset_view",
            "options": {},
        })

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
        self._selections.clear()
        self._region_counter = 0
        self._layer_counter = 0
        self._global_hidden = False
        self.whole = Whole(self)
        self._shape_history.clear()
        self._annotation_history.clear()
        self._measurement_history.clear()
        self._selection_history.clear()
        self._last_label = None

        # Ask frontend to clear everything (molecule + shapes + view)
        self._send(
            {
                "op": "clear_all",
                "options": {},
            }
        )

    @signal(tags=["camera"], extra_factory=lambda args, kwargs: {"pretty": _signal_value(args, kwargs, 1, "pretty")})
    @digest()
    def get_camera_snapshot(self, *, pretty: bool = False, skip_digestion: bool = False) -> dict | str | None:
        """Return the last camera snapshot received from the frontend.

        Parameters
        ----------
        pretty
            If ``True``, return a formatted JSON string instead of a dict.
        """
        if self._last_camera_snapshot is None:
            return None
        if not pretty:
            return dict(self._last_camera_snapshot)
        return json.dumps(self._last_camera_snapshot, indent=2, sort_keys=True)

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

    @signal(tags=["viewer", "query"])
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
        """Apply a previously saved camera snapshot.

        Parameters
        ----------
        snapshot
            Camera snapshot dict (Mol* format).
        duration_ms
            Transition duration in milliseconds.
        """
        if not snapshot:
            return
        duration_value = int(puw.get_value(duration_ms, to_unit="ms")) if puw.is_quantity(duration_ms) else int(duration_ms)
        self._send(
            {
                "op": "set_camera_snapshot",
                "snapshot": snapshot,
                "duration_ms": duration_value,
            }
        )

    @signal(tags=["query"])
    @digest()
    def info(self,
             element='system',
             selection='all',
             syntax='MolSysMT',
             mask='all',
             skip_digestion=False
            ):
        kwargs = dict(
            element=element,
            selection=selection,
            syntax=syntax,
            skip_digestion=True,
        )
        if "mask" in inspect.signature(msm.info).parameters:
            kwargs["mask"] = mask
        return msm.info(self._molsys, **kwargs)

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

    @signal(tags=["query"])
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
    def extract(
        self,
        selection="all",
        structure_indices="all",
        *,
        syntax="MolSysMT",
        debug_js: bool | None = None,
        skip_digestion: bool = False,
    ):
        """Return a new view built from a subset of this view."""
        from .tools.basic.extract import extract as _extract_view

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
        skip_digestion: bool = False,
    ) -> None:
        """Add atoms/structures from another system into this view and refresh the viewer (live)."""
        if self._molsys is None:
            raise ValueError("No molecular system loaded. Load a system before calling add().")

        visible = self.visible_atom_indices
        msm.add(
            self._molsys,
            from_molecular_system,
            selection=selection,
            structure_indices=structure_indices,
            keep_ids=keep_ids,
            in_place=True,
            syntax=syntax,
            skip_digestion=True,
        )
        self.molecular_system = self._molsys
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
            raise RuntimeError("Image export requires a live ready frontend.")

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
        from ._version import __version__ as _pkg_version
        base_version = _pkg_version.split("+", 1)[0]
        runtime_cdn = f"https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@{base_version}/dist/viewer.js"

        ui_config = {
            "show_controls": bool(include_controls),
            "autohide_controls": bool(getattr(self.widget, "autohide_controls", False)),
            "controls_position": list(getattr(self.widget, "controls_position", ["top", "right"])),
            "controls_position_fullscreen": list(getattr(self.widget, "controls_position_fullscreen", ["bottom", "right"])),
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

    def _build_export_messages(self) -> list[dict]:
        """Return the messages to replay when exporting HTML."""
        messages = self._clean_message_history()
        if self._last_camera_snapshot:
            messages.append(
                {
                    "op": "set_camera_snapshot",
                    "snapshot": self._last_camera_snapshot,
                    "duration_ms": 0,
                }
            )
        return messages

    def _clean_message_history(self) -> list[dict]:
        """Remove redundant messages to keep exports lean."""
        deleted_dead_layer_tags = {
            msg.get("tag")
            for msg in self._message_history
            if msg.get("op") == "delete_layer"
            and isinstance(msg.get("tag"), str)
            and msg.get("tag") not in self.layers
        }
        dead_layer_ops = {
            "add_label",
            "update_label",
            "create_layer",
            "show_layer",
            "hide_layer",
            "delete_layer",
        }
        cleaned: list[dict] = []
        for msg in self._message_history:
            if msg.get("op") in dead_layer_ops and msg.get("tag") in deleted_dead_layer_tags:
                continue
            if msg.get("op") == "update_visibility":
                opts = msg.get("options") or {}
                vis = opts.get("visible_atom_indices")
                if vis is None or vis == []:
                    continue
                if isinstance(vis, list) and vis == list(range(len(vis))):
                    # Default "show all" is redundant
                    continue
            cleaned.append(msg)
        return cleaned

    def _json_for_html_script(self, obj: Any) -> str:
        """Serialize JSON safely for embedding inside an HTML <script> tag."""
        text = json.dumps(obj, separators=(",", ":"))
        # Prevent `</script>`-style early termination and reduce HTML parsing surprises.
        return (
            text.replace("&", "\\u0026")
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )
