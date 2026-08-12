"""`enabled` turns a scene effect on or off.

A strict boolean, and here the reason is different from `overwrite`'s. `spin(enabled=0.5)`
reads to a user as "spin at half speed" — the `speed` argument sits right beside it — and
Python would accept it as `True`, spinning at the default speed. The call would look like
it worked and do something else, which is the failure a boolean check is cheapest at
preventing.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_enabled(enabled, caller=None):
    if isinstance(enabled, bool):
        return enabled
    raise ArgumentError(
        "enabled",
        value=enabled,
        caller=caller,
        message="expected True or False; a rate belongs in `speed`",
    )
