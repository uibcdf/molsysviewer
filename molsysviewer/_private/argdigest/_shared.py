"""Checks shared by families of arguments that mean the same thing.

The helpers are **not** named `digest_*`: ArgDigest scans a digester module's namespace
for that prefix, so a shared helper imported into one would be picked up as a digester and
rejected for taking two value parameters.

`time_ms`, `at_time_ms`, `start_time_ms` and `end_time_ms` are one rule stated four times
in the movie timeline; `from_index` and `to_index` are one rule stated twice. Writing four
near-identical digester modules is how they drift, so the rule lives here once and each
digester is the thin thing that names it.

Kept outside `argument/` on purpose: that directory is scanned, and one module per argument
name is the contract it lives by.
"""

from __future__ import annotations

# `molsysviewer._private.exceptions`, not `argdigest.exceptions`: there are two
# `ArgumentError`s and only this one renders its message. The other yields an empty
# string, which reads as a raise with nothing said.
from ..exceptions import ArgumentError


def check_milliseconds(name, value, caller=None, *, allow_none=True):
    """A point on a timeline, in milliseconds from its start.

    Non-negative: a keyframe before the beginning has no meaning, and a negative time
    sorts ahead of everything, silently reordering a timeline the caller wrote in order.
    """
    if value is None:
        if allow_none:
            return None
        raise ArgumentError(name, value=value, caller=caller,
                            message="a time in milliseconds is required here")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ArgumentError(name, value=value, caller=caller,
                            message="expected a time in milliseconds")
    if value < 0:
        raise ArgumentError(name, value=value, caller=caller,
                            message="must be positive or zero: a timeline starts at "
                                    "zero, and a negative time sorts ahead of every "
                                    "keyframe")
    return float(value)


def check_structure_index(name, value, caller=None):
    """A 0-based index into the loaded structures.

    The upper bound is not checked here: it depends on the system currently loaded, which
    a digester does not see. The timeline refuses an out-of-range index when it builds.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArgumentError(name, value=value, caller=caller,
                            message="a structure index is a whole number")
    if value < 0:
        raise ArgumentError(name, value=value, caller=caller,
                            message="structure indices start at zero")
    return value
