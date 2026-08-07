from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw


def digest_extra_radius(extra_radius, caller=None):
    if extra_radius is None:
        return extra_radius
    if puw.is_quantity(extra_radius):
        return puw.standardize(extra_radius)
    if isinstance(extra_radius, (int, float)):
        return puw.quantity(extra_radius, "angstroms", standardized=True)
    if isinstance(extra_radius, str):
        try:
            value = float(extra_radius)
        except ValueError:
            return extra_radius
        return puw.quantity(value, "angstroms", standardized=True)
    raise ArgumentError("extra_radius", value=extra_radius, caller=caller, message=None)
