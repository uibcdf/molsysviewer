from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw


def digest_min_radius(min_radius, caller=None):
    if min_radius is None:
        return min_radius
    if puw.is_quantity(min_radius):
        return puw.standardize(min_radius)
    if isinstance(min_radius, (int, float)):
        return puw.quantity(min_radius, "angstroms", standardized=True)
    if isinstance(min_radius, str):
        try:
            value = float(min_radius)
        except ValueError:
            return min_radius
        return puw.quantity(value, "angstroms", standardized=True)
    raise ArgumentError("min_radius", value=min_radius, caller=caller, message=None)
