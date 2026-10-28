"""Remap scene data through explicit retained or new structure positions.

These operations copy scene metadata, never molecular coordinates or analyses.
They are shared by independent extraction and live molecular adoption.
"""

from copy import deepcopy
from numbers import Integral

import numpy as np


def normalize_structure_index_map(values, old_count, new_count):
    """Validate new-to-old positions; None explicitly declares a new origin."""
    if values is None:
        return None
    if not isinstance(values, (list, tuple, np.ndarray)) or (isinstance(values, np.ndarray) and values.ndim != 1):
        raise ValueError("structure_index_map must be a one-dimensional new-to-old list.")
    if len(values) != new_count or any(
        index is not None
        and (isinstance(index, (bool, np.bool_)) or not isinstance(index, Integral) or not 0 <= index < old_count)
        for index in values
    ):
        raise ValueError("structure_index_map requires a valid old structure index or None per new structure.")
    return [None if index is None else int(index) for index in values]


def remap_structure_filter(values, frames):
    if not isinstance(values, list):
        return values
    selected = set(values)
    return [new for new, old in enumerate(frames) if old in selected]


def remap_current_structure(index, frames):
    """The first retained occurrence is the scalar playhead's destination."""
    return next((new for new, old in enumerate(frames) if old == index), 0)


def remap_shape_structures(record, frames):
    result = deepcopy(record)
    options = result.get("options", {})
    for key, values in list(options.items()):
        if key.startswith("structures_") and isinstance(values, list):
            if None in frames:
                raise ValueError("Clear per-structure shapes before adding structures with new origins.")
            options[key] = [deepcopy(values[index]) for index in frames]
    return result


def remap_trajectory_cards(cards, frames):
    if cards and None in frames:
        raise ValueError("Clear trajectory plot cards before adding structures with new origins.")
    if cards and not frames:
        raise ValueError("Clear trajectory plot cards before removing every structure.")
    result = deepcopy(cards)
    for card in result:
        for series in card["series"]:
            series["values"] = [series["values"][index] for index in frames]
        if "x" in card:
            card["x"] = [card["x"][index] for index in frames]
        card["events"] = [
            dict(event, frame=new)
            for event in card.get("events", [])
            for new, old in enumerate(frames)
            if event["frame"] == old
        ]
        card["n_frames"] = len(frames)
    return result


def prepare_structure_edit(view, frames):
    """Prepare every structure-bound owner before publishing molecular adoption."""
    return {
        "shapes": [remap_shape_structures(record, frames) for record in view._shape_history],
        "filters": [
            (obj, remap_structure_filter(obj._filter["structure_indices"], frames))
            for obj in view.interactions._objects()
        ],
        "cards": remap_trajectory_cards(view.trajectory_plot._cards(), frames),
        "index": remap_current_structure(view.player.index, frames),
    }


def apply_structure_edit(view, prepared):
    view._shape_history = prepared["shapes"]
    for obj, values in prepared["filters"]:
        obj._filter["structure_indices"] = values
    if "trajectory_plot" in view._scene_look:
        view._scene_look["trajectory_plot"] = {
            "op": "set_trajectory_plot",
            "options": {"cards": prepared["cards"]},
        }
    view._current_structure_index = prepared["index"]
