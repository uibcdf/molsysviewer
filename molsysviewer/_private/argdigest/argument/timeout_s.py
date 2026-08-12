"""`timeout_s` is how long to wait for the frontend, in seconds.

Named with its unit rather than digested as a quantity, deliberately: it is a wall-clock
budget for a transport wait, not a physical magnitude of the molecular system. The units
policy governs lengths, positions and the like; a timeout has no place in a unit registry
and would gain nothing from one.

Zero is refused. `wait_for_transaction(timeout_s=0)` reads as "do not wait", but the loop
it feeds would return `False` before the frontend could possibly answer — a poll dressed
as a wait. If that is what a caller wants, they should ask the state directly.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_timeout_s(timeout_s, caller=None):
    if isinstance(timeout_s, bool) or not isinstance(timeout_s, (int, float)):
        raise ArgumentError("timeout_s", value=timeout_s, caller=caller, message=None)
    if timeout_s <= 0:
        raise ArgumentError(
            "timeout_s",
            value=timeout_s,
            caller=caller,
            message="a wait needs a positive number of seconds",
        )
    return float(timeout_s)
