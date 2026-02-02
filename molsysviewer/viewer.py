from __future__ import annotations

from typing import Any, Dict, Mapping
import warnings
import time
import inspect
import json
import re

import molsysmt as msm
import numpy as np

from ._pyunitwizard import puw
from ._private.digestion import digest
from ._private.variables import is_all
from .widget import MolSysViewerWidget
from .loaders import load_from_molsysmt as _load_from_molsysmt
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


class MolSysView:
    """Mol* viewer widget with a Python-facing API.

    Provides structure loading, visibility control, shape management, and
    utilities to export static HTML views for documentation or sharing.
    """
    def _repr_mimebundle_(self, include=None, exclude=None):
        """IPython/Jupyter display hook (delegates to the underlying widget)."""
        return self.widget._repr_mimebundle_(include=include, exclude=exclude)

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
        self._shape_history: list[dict] = []
        self._last_label: str | None = None

        self._regions: Dict[str, Region] = {}
        self._layers: Dict[str, Layer] = {}
        self._region_counter = 0
        self._layer_counter = 0
        self._global_hidden = False

        self.whole = Whole(self)

        # Register callback for JS->Python messages
        def _handle_msg(widget, content, buffers):  # type: ignore[override]
            event = content.get("event")
            if event == "ready":
                self._ready = True
                # As soon as the frontend is ready, flush the pending queue.
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
            elif event == "viewer_init_failed":
                reason = content.get("reason", "unknown")
                message = content.get("message") or "Mol* viewer failed to initialize."
                warnings.warn(
                    f"{message} (reason: {reason})",
                    RuntimeWarning,
                    stacklevel=2,
                )

        self.widget.on_msg(_handle_msg)

        self.molecular_system = None
        self.selection = None
        self.structure_indices = None
        self._molsys = None
        self.atom_mask = None
        self.structure_mask = None

        self.shapes = ShapesManager(self)
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
                        from ._private.digestion import digest_selection_and_syntax

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
        return region

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

    def _shape_tag_from_message(self, msg: dict) -> str | None:
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

        if op == "clear_shapes_by_tag":
            cleared_tag = msg.get("tag")
            if cleared_tag is None:
                self._shape_history.clear()
                return
            if not isinstance(cleared_tag, str):
                return
            self._shape_history = [
                m for m in self._shape_history if self._shape_tag_from_message(m) != cleared_tag
            ]
            return

        if not op.startswith("add_"):
            return

        self._shape_history.append(dict(msg))

    def _send(self, msg: dict) -> None:
        """Send a message to the frontend or queue it if the frontend is not ready yet."""
        self._message_history.append(msg)
        self._record_shape_message(msg)
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

        viewer_json = self._molsys.to_form("molsysmt.ViewerJSON")
        payload = _serialize_molsys_payload(viewer_json)
        if payload is None:
            raise ValueError("Unable to serialize MolSysMT viewer payload")

        n_atoms = int(self._molsys.topology.get_n_atoms())
        n_structures = int(self._molsys.structures.get_n_structures())
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
                **getattr(self.whole, "_repr_params", {}),
            )

        if self._global_hidden:
            self._send({"op": "hide_global", "target": "global"})

        for layer in list(self._layers.values()):
            if not getattr(layer, "_active", True):
                continue
            layer._send_create()  # noqa: SLF001
            if getattr(layer, "_hidden", False):
                layer.hide()

        for region in list(self._regions.values()):
            if not getattr(region, "_active", True):
                continue
            region._send_create()  # noqa: SLF001
            if getattr(region, "preset", None) is not None or region.representation is not None or region.repr_params:
                region.set_representation(
                    region.representation,
                    preset=getattr(region, "preset", None),
                    **(region.repr_params or {}),
                )
            if getattr(region, "_hidden", False):
                region.hide()

        for msg in self._shape_history:
            remapped = self._remap_shape_message(msg, atom_index_map)
            if remapped is None:
                continue
            self._send_replay(remapped)

        self._update_visibility_in_frontend()

    # --- Public loading API ---

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
        duration_ms_value = puw.get_value(duration, to_unit="ms")
        extra_radius = round(float(puw.get_value(extra_radius, to_unit="angstroms")), 6)
        min_radius = round(float(puw.get_value(min_radius, to_unit="angstroms")), 6)

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

    @digest()
    def reset_camera(self, skip_digestion: bool = False) -> None:
        """Reset the camera / view in the frontend."""
        self._send({
            "op": "reset_view",
            "options": {},
        })

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
        self._region_counter = 0
        self._layer_counter = 0
        self._global_hidden = False
        self.whole = Whole(self)
        self._shape_history.clear()
        self._last_label = None

        # Ask frontend to clear everything (molecule + shapes + view)
        self._send(
            {
                "op": "clear_all",
                "options": {},
            }
        )

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
        self._send(
            {
                "op": "set_camera_snapshot",
                "snapshot": snapshot,
                "duration_ms": int(duration_ms),
            }
        )

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
        msm.set(
            self._molsys,
            element=element,
            selection=selection,
            structure_indices=structure_indices,
            syntax=syntax,
            skip_digestion=True,
            **kwargs,
        )
        self.molecular_system = self._molsys
        self._rebuild_view_from_current_molsys(label=self._last_label, visible_atom_indices=visible)

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

    @digest()
    def write_html(
        self,
        output_filename: str,
        *,
        title: str = "MolSysViewer",
        include_controls: bool = True,
        include_popout: bool = True,
        mode: str = "standalone",
        inline_messages: bool = True,
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
            raise ValueError("write_html(mode=...) must be 'standalone' or 'lite'.")

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
  <script type="module">
    const el = document.getElementById("molsysviewer-root");
    const ui = JSON.parse(document.getElementById("molsysviewer-ui").textContent || "{{}}");
    const messages = JSON.parse(document.getElementById("molsysviewer-messages").textContent || "[]");

    const candidates = [
      "{runtime_cdn}",
    ];

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
        cleaned: list[dict] = []
        for msg in self._message_history:
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
