import math

import numpy as np

from molsysviewer._pyunitwizard import puw

from ...exceptions import ArgumentError


def digest_value_range(value_range, caller=None):
    """Digest a scalar color range.

    Accepts ``None`` (the range is inferred from the data), a quantity vector,
    two compatible scalar quantities, or a unit-free ``list``, ``tuple``, or
    one-dimensional ``numpy.ndarray`` of exactly two finite real
    numbers ``(vmin, vmax)`` with ``vmin <= vmax``. Returns a canonical
    ``[vmin, vmax]`` pair of Python ``float``, retaining explicit units when
    supplied. Equal bounds are valid because the
    color mapper deliberately handles a zero span.

    Booleans, non-numeric or non-finite entries, sequences of any other length,
    multidimensional arrays, and reversed bounds are rejected.
    """
    if value_range is None:
        return None
    original = value_range
    try:
        unit = None
        if puw.is_quantity(value_range):
            quantity = puw.ensure_quantity(value_range, standardized=False, caller=caller)
            unit = puw.get_unit(quantity)
            value_range = puw.get_value(quantity, to_unit=unit)
        elif isinstance(value_range, (list, tuple)) and any(puw.is_quantity(v) for v in value_range):
            if len(value_range) != 2 or not all(puw.is_quantity(v) for v in value_range):
                raise TypeError
            quantities = [puw.ensure_quantity(v, standardized=False, caller=caller) for v in value_range]
            unit = puw.get_unit(quantities[0])
            value_range = [puw.get_value(v, to_unit=unit, value_type=float) for v in quantities]
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
        return bounds if unit is None else puw.quantity(bounds, unit)
    except Exception as exc:
        raise ArgumentError("value_range", value=original, caller=caller, message=None) from exc
