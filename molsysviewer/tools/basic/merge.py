from __future__ import annotations

from typing import Any

import molsysmt as msm
import numpy as np
from depdigest import dep_digest
from smonitor import signal

from ..._private.arg_digestion import digest
from ...new_view import new_view
from ...viewer import MolSysView


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


def _remap_shape_message(msg: dict[str, Any], atom_offset: int, tag_map: dict[str, str]) -> dict[str, Any]:
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

    if getattr(primary.whole, "_preset", None) is not None or getattr(primary.whole, "_representation", None) is not None:
        result.whole.set_representation(
            getattr(primary.whole, "_representation", None),
            preset=getattr(primary.whole, "_preset", None),
            skip_digestion=True,
            **(getattr(primary.whole, "_repr_params", {}) or {}),
        )
    if getattr(primary, "_global_hidden", False):  # noqa: SLF001
        result.whole.hide(skip_digestion=True)

    if result.atom_mask is not None:
        result.atom_mask[:] = False

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
            merged_layer = result.new_layer(
                tag=new_tag,
                kind=layer.kind,
                skip_digestion=True,
                **(dict(layer.meta) if isinstance(layer.meta, dict) else {}),
            )
            if getattr(layer, "_hidden", False):
                merged_layer.hide(skip_digestion=True)

        for region in view.regions.values():
            if not getattr(region, "_active", True):
                continue
            new_tag = _unique_tag(region.tag, used_region_tags, source_index)
            remapped_indices = _remap_indices(list(region.atom_indices or []), atom_offset)
            merged_region = result.new_region(
                selection=remapped_indices,
                atom_indices=remapped_indices,
                tag=new_tag,
                representation=None,
                skip_digestion=True,
            )
            if getattr(region, "preset", None) is not None or region.representation is not None or region.repr_params:
                merged_region.set_representation(
                    region.representation,
                    preset=getattr(region, "preset", None),
                    skip_digestion=True,
                    **(region.repr_params or {}),
                )
            if getattr(region, "_hidden", False):
                merged_region.hide(skip_digestion=True)

        for shape_msg in getattr(view, "_shape_history", []):  # noqa: SLF001
            remapped_msg = _remap_shape_message(shape_msg, atom_offset, tag_map)
            result._send(remapped_msg)  # noqa: SLF001

        for original_tag, new_tag in tag_map.items():
            source_layer = view.layers.get(original_tag)
            if source_layer is not None and getattr(source_layer, "_hidden", False):
                result.layers[new_tag].hide(skip_digestion=True)

        visible = getattr(view, "visible_atom_indices", None)
        if visible:
            result.atom_mask[_remap_indices(list(visible), atom_offset)] = True

        atom_offset += int(msm.get(view._molsys, element="system", n_atoms=True, skip_digestion=True))  # noqa: SLF001

    result._update_visibility_in_frontend()  # noqa: SLF001

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
