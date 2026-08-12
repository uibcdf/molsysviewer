"""`invert` flips which side of a clipping plane is discarded.

A strict boolean. Getting it wrong hides exactly the half of the structure the user meant
to keep — a visible, recoverable mistake, but one where a truthy value would give the
wrong half without any indication that the argument was not understood.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_invert(invert, caller=None):
    if isinstance(invert, bool):
        return invert
    raise ArgumentError(
        "invert",
        value=invert,
        caller=caller,
        message="expected True or False; it chooses which side of the plane is cut",
    )
