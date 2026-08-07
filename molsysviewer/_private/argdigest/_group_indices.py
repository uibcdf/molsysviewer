"""Shared validation for fixed-size groups of atom indices."""

import numpy as np

from ..exceptions import ArgumentError


def digest_fixed_size_index_groups(value, size, argument, caller=None):
    """Return a list of ``size``-long lists of non-negative atom indices.

    Accepts any iterable of iterables, including NumPy arrays, and rejects
    groups of the wrong length or with non-integer entries, which would
    otherwise reach the frontend as a malformed mesh.
    """
    if isinstance(value, np.ndarray):
        if value.ndim != 2 or value.shape[1] != size:
            raise ArgumentError(argument, value=value, caller=caller, message=None)
        rows = value.tolist()
    elif isinstance(value, (list, tuple)):
        rows = list(value)
    else:
        raise ArgumentError(argument, value=value, caller=caller, message=None)

    out = []
    for row in rows:
        if isinstance(row, np.ndarray):
            row = row.tolist()
        if not isinstance(row, (list, tuple)) or len(row) != size:
            raise ArgumentError(argument, value=value, caller=caller, message=None)
        group = []
        for index in row:
            if isinstance(index, bool) or not isinstance(index, (int, np.integer)):
                raise ArgumentError(argument, value=value, caller=caller, message=None)
            if int(index) < 0:
                raise ArgumentError(argument, value=value, caller=caller, message=None)
            group.append(int(index))
        out.append(group)

    if not out:
        raise ArgumentError(argument, value=value, caller=caller, message=None)
    return out
