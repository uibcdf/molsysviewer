"""`n_turns` is how many full revolutions a camera orbit performs.

Positive and fractional: half a turn is a legitimate orbit, so this is a float rather than
a count. Zero is refused because an orbit that does not move is a still, and
`add_camera_orbit` would emit `n_keyframes` identical keyframes to express it.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_n_turns(n_turns, caller=None):
    if isinstance(n_turns, bool) or not isinstance(n_turns, (int, float)):
        raise ArgumentError("n_turns", value=n_turns, caller=caller, message=None)
    if n_turns <= 0:
        raise ArgumentError(
            "n_turns",
            value=n_turns,
            caller=caller,
            message="an orbit of zero turns is a still image",
        )
    return float(n_turns)
