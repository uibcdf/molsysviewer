"""Coordinate/offset normalization shared by the annotation API and Studio."""
import numpy as np

from .._pyunitwizard import puw
from .exceptions import ArgumentError


def annotation_vector(value, argument, *, physical=False, caller=None):
    """Resolve a finite triple; legacy bare physical triples explicitly mean nm."""
    try:
        if physical:
            quantity = puw.ensure_quantity(
                puw.quantity(value, "nm") if isinstance(value, (list, tuple, np.ndarray)) else value,
                dimensionality={"[L]": 1},
            )
            array = np.asarray(puw.get_value(quantity, to_unit="angstrom"), dtype=float)
        else:
            if puw.is_quantity(value):
                quantity = puw.ensure_quantity(value, dimensionality={})
                array = np.asarray(puw.get_value(quantity, to_unit="dimensionless"), dtype=float)
            else:
                array = np.asarray(value, dtype=float)
        if array.shape != (3,) or not np.all(np.isfinite(array)):
            raise ValueError("Expected a finite vector of length three.")
        return array.tolist()
    except Exception as exc:
        raise ArgumentError(argument, value=value, caller=caller, message="Requires a finite three-component vector.") from exc
