"""Digest the optional new-to-old structure correspondence for molecular edits."""

from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.structure_correspondence import normalize_structure_index_map


def digest_structure_index_map(structure_index_map, caller=None):
    if structure_index_map is None:
        return None
    try:
        # Domain bounds depend on the scene's old axis and are checked by the
        # adoption boundary even when digestion is explicitly skipped.
        return normalize_structure_index_map(structure_index_map, float("inf"), len(structure_index_map))
    except (TypeError, ValueError) as exc:
        raise ArgumentError("structure_index_map", value=structure_index_map, caller=caller, message=str(exc)) from exc
