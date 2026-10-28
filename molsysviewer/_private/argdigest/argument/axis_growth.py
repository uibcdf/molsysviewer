"""Validate the explicitly received prefix-addition capability."""

from molsysviewer._private.exceptions import ArgumentError


def digest_axis_growth(axis_growth, caller=None):
    if axis_growth in (None, "atoms", "structures"):
        return axis_growth
    raise ArgumentError("axis_growth", value=axis_growth, caller=caller, message="expected None, 'atoms' or 'structures'")
