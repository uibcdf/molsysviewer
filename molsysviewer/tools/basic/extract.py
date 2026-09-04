from __future__ import annotations

from typing import Any

import molsysmt as msm
from depdigest import dep_digest
from smonitor import signal

from ..._private.argdigest import digest

from ...new_view import new_view
from ...viewer import MolSysView


def _build_atom_index_map(molsys: Any, selection: Any, syntax: str) -> dict[int, int]:
    """Return ``{old_atom_index: new_atom_index}`` for the atoms kept by *selection*."""
    selected = msm.select(molsys, selection=selection, syntax=syntax, skip_digestion=False)
    return {int(old): new for new, old in enumerate(selected)}


def _import_extracted_state(
    result: MolSysView,
    source: MolSysView,
    atom_index_map: dict[int, int],
) -> None:
    """Copy scene state from *source* to *result*, remapping atom indices through *atom_index_map*.

    Objects whose atoms are entirely absent from the extraction are dropped.
    Objects with partial atom overlap (regions, world-space shapes) survive with
    the surviving atoms only.
    """

    # ── Global settings ────────────────────────────────────────────────────
    result.widget.show_controls = bool(getattr(source.widget, "show_controls", True))
    result.widget.autohide_controls = bool(getattr(source.widget, "autohide_controls", False))
    result.widget.controls_position = list(
        getattr(source.widget, "controls_position", ["top", "right"])
    )
    result.widget.controls_position_fullscreen = list(
        getattr(source.widget, "controls_position_fullscreen", ["bottom", "right"])
    )
    result._last_label = getattr(source, "_last_label", None)  # noqa: SLF001
    result._last_camera_snapshot = (  # noqa: SLF001
        dict(source._last_camera_snapshot)  # noqa: SLF001
        if isinstance(source._last_camera_snapshot, dict)  # noqa: SLF001
        else None
    )

    # Propagate auto-tag counters so new additions don't collide with migrated tags.
    result._annotation_counter = getattr(source, "_annotation_counter", 0)  # noqa: SLF001
    result._measurement_counter = getattr(source, "_measurement_counter", 0)  # noqa: SLF001
    result._shape_counter = getattr(source, "_shape_counter", 0)  # noqa: SLF001
    result._section_counter = getattr(source, "_section_counter", 0)  # noqa: SLF001

    # Whole representation
    if source.whole.preset is not None or source.whole.representation is not None:
        result.whole.set_representation(
            source.whole.representation,
            preset=source.whole.preset,
            skip_digestion=True,
            **source.whole.params,
        )
    if not source.whole.visible:
        result.whole.hide(skip_digestion=True)

    # ── Layers ─────────────────────────────────────────────────────────────
    for layer in source.layers.values():
        if not getattr(layer, "_active", True):
            continue
        new_layer = result.layers.add(
            layer.tag,
            kind=layer.kind,
            meta=dict(layer.meta) if isinstance(layer.meta, dict) else {},
            skip_digestion=True,
        )
        if getattr(layer, "_hidden", False):
            new_layer.hide(skip_digestion=True)

    # ── Regions ────────────────────────────────────────────────────────────
    # Migrate any region that has at least one atom in the extracted subset.
    for region in source.regions.values():
        if not getattr(region, "_active", True):
            continue
        remapped_indices = [
            atom_index_map[int(i)]
            for i in (region.atom_indices or [])
            if int(i) in atom_index_map
        ]
        if not remapped_indices:
            continue
        new_region = result.regions.add(
            selection=remapped_indices,
            atom_indices=remapped_indices,
            tag=region.tag,
            representation=None,
            skip_digestion=True,
        )
        if region.representation is not None or getattr(region, "preset", None) is not None:
            new_region.set_representation(
                region.representation,
                preset=getattr(region, "preset", None),
                skip_digestion=True,
                **(region.repr_params or {}),
            )
        if getattr(region, "_hidden", False):
            new_region.hide(skip_digestion=True)

    # An overlay arrives in two halves, and migrating only one is what
    # `uibcdf/molsysviewer#74` was: the replayable message, which `records()` reads and
    # which `_send` records on its own, and the Python object in `_scene_objects`, which
    # `tags()` and `get()` read and which nothing here used to create. A view missing the
    # second half draws correctly and then raises `AttributeError` the first time
    # `export_state` resolves a record through `get()` -- so it could not be saved, and
    # any scene-recording operation on it crashed.
    #
    # `_send` records the message, exactly as it does on the normal add path. Appending
    # here as well is what doubled shapes and annotations; measurements escaped only
    # because their recorder de-duplicates by tag.

    # ── Shapes ─────────────────────────────────────────────────────────────
    # _remap_shape_message returns None for atom-anchored shapes whose atoms
    # are entirely absent; world-space shapes (no atom_indices) always pass.
    for msg in getattr(source, "_shape_history", []):  # noqa: SLF001
        remapped = source._remap_shape_message(msg, atom_index_map)  # noqa: SLF001
        if remapped is not None:
            _register_overlay(result, "shape", remapped)
            result._send(remapped)  # noqa: SLF001

    # ── Annotations ────────────────────────────────────────────────────────
    for msg in getattr(source, "_annotation_history", []):  # noqa: SLF001
        remapped = source._remap_shape_message(msg, atom_index_map)  # noqa: SLF001
        if remapped is not None:
            _register_overlay(result, "annotation", remapped)
            result._send(remapped)  # noqa: SLF001

    # ── Measurements ───────────────────────────────────────────────────────
    # Only migrate when all endpoint atoms survive.
    for msg in getattr(source, "_measurement_history", []):  # noqa: SLF001
        remapped = source._remap_measurement_message(msg, atom_index_map)  # noqa: SLF001
        if remapped is not None:
            _register_overlay(result, "measurement", remapped)
            result._send(remapped)  # noqa: SLF001

    # ── Saved selections ───────────────────────────────────────────────────
    for msg in getattr(source, "_selection_history", []):  # noqa: SLF001
        remapped = source._remap_selection_message(msg, atom_index_map)  # noqa: SLF001
        if remapped is not None:
            result._selection_history.append(remapped)  # noqa: SLF001
            result._send(remapped)  # noqa: SLF001

    # ── Sections (world-space — always migrate) ────────────────────────────
    for record in getattr(source, "_section_history", []):  # noqa: SLF001
        result._section_history.append(dict(record))  # noqa: SLF001
    if result._section_history:  # noqa: SLF001
        result._send({"op": "set_sections", "sections": list(result._section_history)})  # noqa: SLF001

    # ── Atom visibility ────────────────────────────────────────────────────
    if result._atom_mask is not None:
        result._atom_mask[:] = False
    visible = source._visible_atom_indices
    if visible and result._atom_mask is not None:
        remapped_visible = [
            atom_index_map[int(i)] for i in visible if int(i) in atom_index_map
        ]
        if remapped_visible:
            result._atom_mask[remapped_visible] = True
    result._update_visibility_in_frontend()  # noqa: SLF001

    # ── Box ────────────────────────────────────────────────────────────────
    box_record = getattr(source, "_box_record", None)
    if box_record is not None:
        result.show_box(
            color=box_record["color"],
            width=box_record["width"],
            alpha=box_record["alpha"],
            structure_indices=0,
            skip_digestion=True,
        )

    # ── Per-atom colors ────────────────────────────────────────────────────
    atom_color_map = getattr(source, "_atom_color_map", {})
    if atom_color_map:
        remapped_colors = {
            atom_index_map[k]: v
            for k, v in atom_color_map.items()
            if k in atom_index_map
        }
        if remapped_colors:
            result._atom_color_map = remapped_colors  # noqa: SLF001
            result._send(  # noqa: SLF001
                {
                    "op": "set_atom_colors",
                    "atom_indices": list(remapped_colors.keys()),
                    "colors": list(remapped_colors.values()),
                    "replace": True,
                }
            )

    # ── Camera ─────────────────────────────────────────────────────────────
    if result._last_camera_snapshot:  # noqa: SLF001
        result.set_camera_snapshot(
            result._last_camera_snapshot,  # noqa: SLF001
            duration_ms=0,
            skip_digestion=True,
        )


@dep_digest("molsysmt")
@signal(tags=["tools", "basic", "extract"])
@digest()
def extract(
    view: Any,
    selection: Any = "all",
    structure_indices: Any = "all",
    *,
    syntax: str = "MolSysMT",
    debug_js: bool | None = None,
    skip_digestion: bool = False,
):
    """Return a new view built from a structural subset of an existing view.

    Unlike a plain structural extract, the relevant scene state is migrated to
    the new view with atom indices remapped to the extracted subset:

    * **Regions** — recreated for any region that has at least one atom in the
      selection (surviving atoms only).
    * **Shapes** — atom-anchored shapes are migrated only if their anchor atoms
      survive; world-space shapes (no atom reference) are always migrated.
    * **Measurements** — migrated only when every endpoint atom survives.
    * **Annotations** — migrated only when their anchor atoms survive.
    * **Saved selections** — remapped; dropped if no atoms survive.
    * **Sections** — always migrated (world-space clipping planes).
    * **Global settings** — whole representation, background, camera snapshot,
      and widget controls are copied from the source.

    Parameters
    ----------
    view
        Source ``MolSysView``.
    selection
        Atom selection expression (default ``"all"``).
    structure_indices
        Structure / frame indices to keep (default ``"all"``).
    syntax
        Selection syntax (default ``"MolSysMT"``).
    debug_js
        Override the JS debug flag.  Defaults to the source view's setting.
    """
    atom_index_map = _build_atom_index_map(view._molsys, selection, syntax)  # noqa: SLF001

    extracted = msm.extract(
        view._molsys,  # noqa: SLF001
        selection=selection,
        structure_indices=structure_indices,
        to_form="molsysmt.MolSys",
        syntax=syntax,
        skip_digestion=False,
    )
    result = new_view(
        extracted,
        selection="all",
        structure_indices="all",
        syntax=syntax,
        debug_js=view._debug_js if debug_js is None else debug_js,  # noqa: SLF001
        skip_digestion=True,
    )
    _import_extracted_state(result, view, atom_index_map)
    return result


def _register_overlay(view, kind: str, message: dict) -> None:
    """Create the Python object for a migrated overlay, the way its own add path does.

    Registration happens *before* the message is sent, matching the normal path, where
    `_ensure_layer` runs and only then `_send`: `_send` synchronises scene-object
    summaries, and it has to find the object to summarise it.

    A message that carries no usable tag is skipped rather than guessed at: it will still
    draw, which is what it did before, and inventing a tag would be worse than the gap.
    """
    # `_tag_from_message` because the shape ops carry their tag inside `options` while
    # annotations and measurements carry it at the top level. Reading only the top level
    # silently skipped every shape.
    tag = view._tag_from_message(message)  # noqa: SLF001
    if not tag:
        return
    options = message.get("options") or {}
    layer_tag = options.get("layer_tag")
    layer_tag = layer_tag if isinstance(layer_tag, str) and layer_tag else None

    if kind == "shape":
        from ...shapes._registry import register_shape_layer

        register_shape_layer(view, tag, layer_tag=layer_tag)
        return

    collection = getattr(view, "annotations" if kind == "annotation" else "measurements")
    collection._ensure_layer(tag, layer_tag=layer_tag)  # noqa: SLF001
