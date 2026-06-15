import numpy as np

from ...exceptions import ArgumentError


def digest_coordinate_pairs(coordinate_pairs, caller=None):
    """Validate and normalize ``coordinate_pairs`` to a nested list of shape
    ``(n, 2, 3)`` in nanometers.

    Mirrors the MolSysMT ``digest_coordinates`` pattern: PyUnitWizard
    ``Quantity`` inputs are accepted natively (their length dimensionality is
    validated and the value is converted to the suite-native nanometer), while
    plain nested lists / tuples / ndarrays are accepted unit-less and unchanged.
    """
    if coordinate_pairs is None:
        return None

    from molsysviewer import pyunitwizard as puw

    try:
        if puw.is_quantity(coordinate_pairs):
            unit = puw.get_unit(coordinate_pairs)
            if not puw.check(unit, dimensionality={"[L]": 1}):
                raise ValueError("coordinate_pairs must have length units")
            value = np.asarray(puw.get_value(coordinate_pairs, to_unit="nm"), dtype=float)
        else:
            value = np.asarray(coordinate_pairs, dtype=float)

        if value.ndim != 3 or value.shape[1] != 2 or value.shape[2] != 3:
            raise ValueError("coordinate_pairs must have shape (n, 2, 3)")

        return value.tolist()

    except ArgumentError:
        raise
    except Exception:
        raise ArgumentError(
            "coordinate_pairs", value=coordinate_pairs, caller=caller, message=None
        ) from None
