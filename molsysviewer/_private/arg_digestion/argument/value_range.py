import math

import numpy as np

from ...exceptions import ArgumentError


def digest_value_range(value_range, caller=None):
    """Digest a scalar color range.

    Accepts ``None`` (the range is inferred from the data) or a ``list``,
    ``tuple``, or one-dimensional ``numpy.ndarray`` of exactly two finite real
    numbers ``(vmin, vmax)`` with ``vmin <= vmax``. Returns a canonical
    ``[vmin, vmax]`` pair of Python ``float``. Equal bounds are valid because the
    color mapper deliberately handles a zero span.

    Booleans, non-numeric or non-finite entries, sequences of any other length,
    multidimensional arrays, and reversed bounds are rejected.
    """
    if value_range is None:
        return None
    try:
        if isinstance(value_range, np.ndarray):
            if value_range.ndim != 1 or value_range.shape[0] != 2:
                raise TypeError
            pair = [value_range[0], value_range[1]]
        elif isinstance(value_range, (list, tuple)):
            if len(value_range) != 2:
                raise TypeError
            pair = list(value_range)
        else:
            raise TypeError

        bounds = []
        for v in pair:
            if isinstance(v, bool) or not isinstance(v, (int, float, np.number)):
                raise TypeError
            fv = float(v)
            if not math.isfinite(fv):
                raise ValueError
            bounds.append(fv)

        if bounds[0] > bounds[1]:
            raise ValueError
        return bounds
    except (TypeError, ValueError) as exc:
        raise ArgumentError("value_range", value=value_range, caller=caller, message=None) from exc
