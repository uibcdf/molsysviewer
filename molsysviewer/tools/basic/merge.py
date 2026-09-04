from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np
from depdigest import dep_digest
from smonitor import signal

from ..._private.argdigest import digest
from ...new_view import new_view
from ...viewer import MolSysView


class _OffsetMap:
    """Proxy dict for offset-based atom index remapping (merge use case).

    All source atoms survive the merge, so ``get`` always returns
    ``key + offset``.  This is compatible with the ``dict.get`` protocol used
    by ``MolSysView._remap_measurement_message`` and
    ``MolSysView._remap_selection_message``.
    """

    __slots__ = ("_offset",)

    def __init__(self, offset: int) -> None:
        self._offset = offset

    def get(self, key: int, default: int | None = None) -> int:  # noqa: ARG002
        return key + self._offset


def _remap_indices(indices: Any, atom_offset: int) -> list[int]:
    if not isinstance(indices, (list, tuple)):
        return []
    return [int(ii) + atom_offset for ii in indices if isinstance(ii, (int, np.integer))]


def _remap_atom_pairs(pairs: Any, atom_offset: int) -> list[list[int]] | None:
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
            out.append([int(pair[0]) + atom_offset, int(pair[1]) + atom_offset])
    return out


def _remap_tagged_message(msg: dict[str, Any], atom_offset: int, tag_map: dict[str, str]) -> dict[str, Any]:
    remapped = dict(msg)
    options = remapped.get("options")
    if not isinstance(options, dict):
        return remapped

    options = dict(options)
    remapped["options"] = options

    tag = options.get("tag")
    if isinstance(tag, str) and tag in tag_map:
        options["tag"] = tag_map[tag]

    if "atom_indices" in options:
        options["atom_indices"] = _remap_indices(options.get("atom_indices"), atom_offset)

    if "mouth_atom_indices" in options:
        mouths = options.get("mouth_atom_indices")
        if isinstance(mouths, list) and mouths and isinstance(mouths[0], list):
            options["mouth_atom_indices"] = [
                _remap_indices(mouth, atom_offset) for mouth in mouths
            ]
        else:
            options["mouth_atom_indices"] = _remap_indices(mouths, atom_offset)

    if "atom_pairs" in options:
        options["atom_pairs"] = _remap_atom_pairs(options.get("atom_pairs"), atom_offset)

    return remapped


def _unique_tag(tag: str, used_tags: set[str], source_index: int) -> str:
    if tag not in used_tags:
        used_tags.add(tag)
        return tag

    base = f"{tag}__{source_index + 1}"
    candidate = base
    counter = 2
    while candidate in used_tags:
        candidate = f"{base}_{counter}"
        counter += 1
    used_tags.add(candidate)
    return candidate


def _import_view_state(result: MolSysView, source_views: list[MolSysView]) -> None:
    primary = source_views[0]
    result.widget.show_controls = bool(getattr(primary.widget, "show_controls", True))
    result.widget.autohide_controls = bool(getattr(primary.widget, "autohide_controls", False))
    result.widget.controls_position = list(getattr(primary.widget, "controls_position", ["top", "right"]))
    result.widget.controls_position_fullscreen = list(
        getattr(primary.widget, "controls_position_fullscreen", ["bottom", "right"])
    )
    result._last_label = getattr(primary, "_last_label", None)  # noqa: SLF001
    result._last_camera_snapshot = (
        dict(primary._last_camera_snapshot)  # noqa: SLF001
        if isinstance(primary._last_camera_snapshot, dict)  # noqa: SLF001
        else None
    )

    if primary.whole.preset is not None or primary.whole.representation is not None:
        result.whole.set_representation(
            primary.whole.representation,
            preset=primary.whole.preset,
            skip_digestion=True,
            **primary.whole.params,
        )
    if not primary.whole.visible:
        result.whole.hide(skip_digestion=True)

    atom_offset = 0
    used_region_tags: set[str] = set()
    used_layer_tags: set[str] = set()

    for source_index, view in enumerate(source_views):
        tag_map: dict[str, str] = {}

        for layer in view.layers.values():
            if not getattr(layer, "_active", True):
                continue
            new_tag = _unique_tag(layer.tag, used_layer_tags, source_index)
            tag_map[layer.tag] = new_tag
            merged_layer = result.layers.add(
                new_tag,
                kind=layer.kind,
                meta=dict(layer.meta) if isinstance(layer.meta, dict) else {},
                skip_digestion=True,
            )
            if getattr(layer, "_hidden", False):
                merged_layer.hide(skip_digestion=True)

        for region in view.regions.values():
            if not getattr(region, "_active", True):
                continue
            new_tag = _unique_tag(region.tag, used_region_tags, source_index)
            remapped_indices = _remap_indices(list(region.atom_indices or []), atom_offset)
            merged_region = result.regions.add(
                selection=remapped_indices,
                atom_indices=remapped_indices,
                tag=new_tag,
                representation=None,
                skip_digestion=True,
            )
            if getattr(region, "preset", None) is not None or region.representation is not None:
                merged_region.set_representation(
                    region.representation,
                    preset=getattr(region, "preset", None),
                    skip_digestion=True,
                    **(region.repr_params or {}),
                )
            if getattr(region, "_hidden", False):
                merged_region.hide(skip_digestion=True)

        for shape_msg in getattr(view, "_shape_history", []):  # noqa: SLF001
            remapped_msg = _remap_tagged_message(shape_msg, atom_offset, tag_map)
            result._send(remapped_msg)  # noqa: SLF001

        for annotation_msg in getattr(view, "_annotation_history", []):  # noqa: SLF001
            remapped_msg = _remap_tagged_message(annotation_msg, atom_offset, tag_map)
            result._send(remapped_msg)  # noqa: SLF001

        # ── Measurements ───────────────────────────────────────────────────
        offset_map = _OffsetMap(atom_offset)
        for measurement_msg in getattr(view, "_measurement_history", []):  # noqa: SLF001
            remapped = result._remap_measurement_message(measurement_msg, offset_map)  # noqa: SLF001
            if remapped is not None:
                result._measurement_history.append(remapped)  # noqa: SLF001
                result._send(remapped)  # noqa: SLF001

        # ── Saved selections ───────────────────────────────────────────────
        for selection_msg in getattr(view, "_selection_history", []):  # noqa: SLF001
            remapped = result._remap_selection_message(selection_msg, offset_map)  # noqa: SLF001
            if remapped is not None:
                result._selection_history.append(remapped)  # noqa: SLF001
                result._send(remapped)  # noqa: SLF001

        for original_tag, new_tag in tag_map.items():
            source_layer = view.layers.get(original_tag)
            if source_layer is not None and getattr(source_layer, "_hidden", False):
                result.layers[new_tag].hide(skip_digestion=True)

        # ── Per-atom colors (accumulated with offset) ──────────────────────
        atom_color_map = getattr(view, "_atom_color_map", {})
        for old_idx, color_int in atom_color_map.items():
            result._atom_color_map[old_idx + atom_offset] = color_int  # noqa: SLF001

        atom_offset += int(msm.get(view._molsys, element="system", n_atoms=True, skip_digestion=True))  # noqa: SLF001

    # ── Per-atom colors — send accumulated map to frontend ─────────────────
    if result._atom_color_map:  # noqa: SLF001
        result._send(  # noqa: SLF001
            {
                "op": "set_atom_colors",
                "atom_indices": list(result._atom_color_map.keys()),  # noqa: SLF001
                "colors": list(result._atom_color_map.values()),  # noqa: SLF001
                "replace": True,
            }
        )

    # ── Box — take from the first source that had one ─────────────────────
    box_record = None
    for view in source_views:
        box_record = getattr(view, "_box_record", None)
        if box_record is not None:
            break
    if box_record is not None:
        result.show_box(
            color=box_record["color"],
            width=box_record["width"],
            alpha=box_record["alpha"],
            structure_indices=0,
            skip_digestion=True,
        )

    if result._last_camera_snapshot:
        result.set_camera_snapshot(result._last_camera_snapshot, duration_ms=0, skip_digestion=True)


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "view"])
@digest()
def merge(
    views: Any,
    *,
    keep_ids: bool = True,
    debug_js: bool | None = None,
    skip_digestion: bool = False,
) -> MolSysView:
    """Return a new view built by merging multiple existing views.

    The merged view uses the first input view as the source of global state
    (whole representation, controls, and last camera snapshot). Regions, layers,
    shapes, and atom visibility from all views are imported. Tag collisions are
    resolved deterministically by suffixing later duplicates with ``__N``.
    """

    source_views = list(views)
    merged = msm.merge(
        [view._molsys for view in source_views],  # noqa: SLF001
        keep_ids=keep_ids,
        to_form="molsysmt.MolSys",
        skip_digestion=True,
    )

    result = new_view(
        merged,
        selection="all",
        structure_indices="all",
        debug_js=debug_js,
        skip_digestion=True,
    )
    _import_view_state(result, source_views)
    return result
