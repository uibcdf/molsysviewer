"""Validate interaction argument shapes; scientific choices stay provider-owned."""

import numpy as np

from molsysviewer._pyunitwizard import puw

from ..exceptions import ArgumentError


def digest_text(value, argument, caller=None, *, optional=False):
    if optional and value is None:
        return None
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ArgumentError(argument, value=value, caller=caller)


def digest_positive_integer(value, argument, caller=None):
    if isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_)) and value > 0:
        return int(value)
    raise ArgumentError(argument, value=value, caller=caller)


def digest_angle(value, argument, caller=None):
    if value is None:
        return None
    try:
        parsed = puw.parse.parse(value) if isinstance(value, str) else value
        if puw.is_quantity(parsed) and puw.are_compatible(parsed, "1 radian"):
            return puw.standardize(parsed)
    except Exception as exc:
        raise ArgumentError(argument, value=value, caller=caller) from exc
    raise ArgumentError(argument, value=value, caller=caller)


def digest_angle_range(value, argument, caller=None):
    if value is None:
        return None
    try:
        if not puw.is_quantity(value) and len(value) == 2:
            parts = [digest_angle(item, argument, caller) for item in value]
            if any(item is None for item in parts):
                raise ArgumentError(argument, value=value, caller=caller)
            magnitudes = np.asarray([puw.get_value(item, to_unit="radians") for item in parts])
            if magnitudes.shape != (2,):
                raise ArgumentError(argument, value=value, caller=caller)
            # The provider accepts one vector quantity, not a tuple of quantities.
            value = puw.quantity(magnitudes, "radians")
        if puw.is_quantity(value):
            if np.asarray(puw.get_value(value)).shape == (2,) and puw.are_compatible(value, "1 radian"):
                return puw.standardize(value)
            raise ArgumentError(argument, value=value, caller=caller)
    except (TypeError, ValueError) as exc:
        raise ArgumentError(argument, value=value, caller=caller) from exc
    raise ArgumentError(argument, value=value, caller=caller)


def digest_index_array(value, argument, caller=None, *, pairs=False):
    if value is None:
        return None
    if isinstance(value, (bool, np.bool_)):
        raise ArgumentError(argument, value=value, caller=caller)
    # Reject booleans before NumPy can coerce a mixed integer/bool list.
    objects = np.asarray(value, dtype=object)
    if any(isinstance(item, (bool, np.bool_)) for item in objects.flat):
        raise ArgumentError(argument, value=value, caller=caller)
    array = np.asarray(value)
    if array.size == 0:
        array = np.empty((0, 2) if pairs else (0,), dtype=np.int64)
    valid_shape = array.ndim == 2 and array.shape[1] == 2 if pairs else array.ndim == 1
    if valid_shape and array.dtype.kind in "iu" and not np.any(array < 0):
        return array
    raise ArgumentError(argument, value=value, caller=caller)
