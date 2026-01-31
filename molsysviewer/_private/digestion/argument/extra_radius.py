from molsysviewer._private.exceptions import ArgumentError
from molsysmt import pyunitwizard as puw


def digest_extra_radius(extra_radius, caller=None):
    if extra_radius is None:
        return extra_radius
    if puw.is_quantity(extra_radius):
        return puw.standardize(extra_radius)
    if isinstance(extra_radius, (int, float, str)):
        return extra_radius
    raise ArgumentError("extra_radius", value=extra_radius, caller=caller, message=None)
