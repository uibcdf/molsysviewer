from molsysviewer._private.exceptions import ArgumentError
from molsysmt import pyunitwizard as puw


def digest_min_radius(min_radius, caller=None):
    if min_radius is None:
        return min_radius
    if puw.is_quantity(min_radius):
        return puw.standardize(min_radius)
    if isinstance(min_radius, (int, float, str)):
        return min_radius
    raise ArgumentError("min_radius", value=min_radius, caller=caller, message=None)
