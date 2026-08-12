"""`overwrite` decides whether registering over an existing name is allowed.

A strict boolean, for the same reason as `clear_first`: the true branch destroys something
a user registered earlier, and a merely truthy value would do it while looking like it was
asked to. The registries refuse a duplicate name by default precisely so that a collision
is visible.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_overwrite(overwrite, caller=None):
    if isinstance(overwrite, bool):
        return overwrite
    raise ArgumentError(
        "overwrite",
        value=overwrite,
        caller=caller,
        message="expected True or False; True replaces an existing registration",
    )
