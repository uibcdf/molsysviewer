"""`loop` decides whether movie playback restarts at the end.

A strict boolean. `play(loop=3)` reads as "loop three times" and Python would take it as
`True`, looping forever — a call that looks like it worked and does something else, with
no way to stop it from the same script.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_loop(loop, caller=None):
    if isinstance(loop, bool):
        return loop
    raise ArgumentError(
        "loop",
        value=loop,
        caller=caller,
        message="expected True or False; a repeat count is not supported",
    )
