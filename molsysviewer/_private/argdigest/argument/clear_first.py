"""`clear_first` chooses whether an import replaces the scene or adds to it.

A strict boolean rather than a truthy test, and the reason is the cost of being wrong:
`clear_first=True` deletes every region, overlay and measurement in the scene before
restoring. A value that is merely truthy — a non-empty string, a stray `1` from a config
file — would erase a user's work while looking like it was asked to.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_clear_first(clear_first, caller=None):
    if isinstance(clear_first, bool):
        return clear_first
    raise ArgumentError(
        "clear_first",
        value=clear_first,
        caller=caller,
        message="expected True or False; this decides whether the scene is erased first",
    )
