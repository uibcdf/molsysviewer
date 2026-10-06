"""Canonical visual query modes and migration of known saved filter fields."""

from copy import deepcopy

QUERY_MODES = frozenset(
    {
        "involving_selection",
        "within_selection",
        "across_selection_boundary",
        "between_selections",
    }
)

_LEGACY_QUERY_MODES = {
    "incident": "involving_selection",
    "internal": "within_selection",
    "cross": "across_selection_boundary",
    "between": "between_selections",
}


def migrate_saved_query_filter(filter_record, *, version):
    """Copy a saved visual filter, migrating extension-v1 query names only."""
    result = deepcopy(filter_record)
    mode = result.get("mode")
    if version == 1 and isinstance(mode, str):
        mode = _LEGACY_QUERY_MODES.get(mode, mode)
    if not isinstance(mode, str) or mode not in QUERY_MODES:
        raise ValueError("Invalid saved interaction query mode.")
    result["mode"] = mode
    return result
