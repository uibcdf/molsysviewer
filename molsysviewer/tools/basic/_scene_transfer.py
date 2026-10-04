"""Transfer the canonical scene with explicit atom and structure correspondences."""

import re
from copy import deepcopy

from ...interactions import _analysis_signature
from ...loaders._source_records import _remap_source_records


def _transfer_state(source, target, atom_map=None, frames=None, *, merge=False):
    state = deepcopy(source.export_state())
    if atom_map is None and frames is None:
        return state

    def atoms(values):
        return [atom_map[int(i)] for i in values if int(i) in atom_map]

    def colors(values):
        return {str(atom_map[int(i)]): color for i, color in values.items() if int(i) in atom_map}

    changed_indices = merge or len(atom_map) != source.molsys.get_n_atoms() or any(i != j for i, j in atom_map.items())
    state["structure"] = target._structure_identity()
    if "sources" in state:
        state["sources"] = {
            "version": 1,
            "binding": target._source_state_binding(),
            "records": _remap_source_records(state["sources"]["records"], atom_map, frames),
        }
    state["whole"]["color_layer"] = colors(state["whole"].get("color_layer", {}))
    for record in state["regions"]:
        region = source.regions[record["tag"]]
        record["atom_indices"] = atoms(region.atom_indices or [])
        record["color_layer"] = colors(record.get("color_layer", {}))
        recipe = record["provenance"]
        if recipe.get("kind") == "active_selection":
            recipe["atom_indices"] = atoms(recipe.get("atom_indices", []))
        # Local hierarchy indices and a source-wide query cannot be replayed in
        # a different index space. Preserve the original recipe as evidence.
        if changed_indices and (
            recipe.get("kind") == "split"
            or (recipe.get("kind") == "query" and (merge or re.search(r"\b\w+_index\b", recipe.get("expression", ""))))
        ):
            record["provenance"] = {
                "kind": "transferred",
                "source_recipe": recipe,
                "broken": True,
                "frame_dependent": False,
            }
            record["mode"] = "static"
        elif record["mode"] == "dynamic":
            record.pop("atom_indices", None)
    # Keep empty operands required by a surviving region's recipe.
    needed = set()
    for record in state["regions"]:
        needed.update(source.regions[record["tag"]]._dependency_uids_from_provenance(record["provenance"]))
    state["regions"] = [r for r in state["regions"] if r.get("atom_indices", True) or r["uid"] in needed]
    shapes = []
    for record in state["shapes"]:
        options = record["options"]
        if frames is not None:
            for key, value in list(options.items()):
                if key.startswith("structures_") and isinstance(value, list):
                    options[key] = [value[i] for i in frames]
        remapped = target._remap_shape_message(record, atom_map)
        if remapped is not None:
            shapes.append(remapped)
    state["shapes"] = shapes
    annotations = []
    for record in state["annotations"]:
        anchor = record["anchor"]
        if anchor.get("type") == "position":
            annotations.append(record)
            continue
        anchor["indices"] = atoms(anchor["indices"])
        anchor["identity"] = target._identities_for(anchor["indices"])
        if anchor["indices"]:
            annotations.append(record)
    state["annotations"] = annotations
    state["measurements"] = [target._remap_measurement_message(r, atom_map) for r in state["measurements"]]
    selections = []
    for record in state["selections"]:
        remapped = target._remap_selection_message(record, atom_map)
        if remapped is not None:
            remapped["identity"] = target._identities_for(remapped["atom_indices"])
            selections.append(remapped)
    state["selections"] = selections
    state["active_selection"]["atom_indices"] = atoms(state["active_selection"]["atom_indices"])
    frame_map = None
    if frames is not None:
        frame_map = {}
        for new, old in enumerate(frames):
            # A scalar current frame selects the first retained copy. Visual
            # filters below retain every destination, including repetitions.
            frame_map.setdefault(old, new)
    for record in state.get("interactions", []):
        scope = record["filter"]
        missing = False
        for key in ("selection", "selection_2"):
            values = scope.get(key)
            if isinstance(values, list):
                missing |= any(i not in atom_map for i in values)
                scope[key] = atoms(values)
        if frame_map is not None and isinstance(scope.get("structure_indices"), list):
            selected_frames = set(scope["structure_indices"])
            scope["structure_indices"] = [new for new, old in enumerate(frames) if old in selected_frames]
        analysis = target._molsys.interactions.get(record["analysis_name"])
        if missing or analysis is None:
            record["broken"] = True
        else:
            record["analysis_revision"] = _analysis_signature(analysis)
    if frame_map is not None:
        view = state.get("view", {})
        view["structure_index"] = frame_map.get(view.get("structure_index", 0), 0)
        for card in state.get("trajectory_plots", []):
            for series in card["series"]:
                series["values"] = [series["values"][i] for i in frames]
            if "x" in card:
                card["x"] = [card["x"][i] for i in frames]
            card["events"] = [
                dict(event, frame=new)
                for event in card.get("events", [])
                for new, old in enumerate(frames)
                if event["frame"] == old
            ]
            card["n_frames"] = len(frames)
    return state


def _copy_auxiliary(source, target, atom_index_map=None):
    for name in ("show_controls", "autohide_controls", "controls_position", "controls_position_fullscreen"):
        setattr(target.widget, name, deepcopy(getattr(source.widget, name)))
    target._last_label = source._last_label
    plot = deepcopy(target._scene_look.get("trajectory_plot"))
    target._scene_look = {}
    for message in deepcopy(source._scene_look).values():
        if message.get("op") == "set_trajectory_plot":
            continue
        message = target._remap_scene_look_message(message, atom_index_map)
        if message is not None:
            target._send(message)
    if plot is not None:
        target._send(plot)
    if source._box_record is not None:
        box = source._box_record
        target.show_box(
            color=box["color"],
            width=box["width"],
            alpha=box["alpha"],
            structure_indices=target.player.index,
            skip_digestion=True,
        )
