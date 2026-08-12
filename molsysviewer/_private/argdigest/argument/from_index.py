"""`from_index` bounds a structure sweep. See `_shared.check_structure_index`."""

from .._shared import check_structure_index


def digest_from_index(from_index, caller=None):
    return check_structure_index("from_index", from_index, caller=caller)
