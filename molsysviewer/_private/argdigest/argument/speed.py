"""`speed` is the rate of a camera animation, in Mol*'s own units.

Positive, or `None` to keep Mol*'s default (~0.1 spinning, ~0.25 swinging). Zero is
refused: `spin(enabled=True, speed=0)` claims to spin and does not, which is worse than
either spinning or refusing, because nothing in the scene says the call was understood.

No upper bound. Mol* accepts a fast spin, and an arbitrary ceiling here would be this
library inventing a limit the renderer does not have.

Deliberately not a `pyunitwizard` quantity: it is a renderer-internal rate, not a physical
magnitude of the molecular system, and the units policy governs the latter.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_speed(speed, caller=None):
    if speed is None:
        return None
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
        raise ArgumentError("speed", value=speed, caller=caller, message=None)
    if speed <= 0:
        raise ArgumentError(
            "speed",
            value=speed,
            caller=caller,
            message="a speed of zero claims to animate and does not; use enabled=False",
        )
    return float(speed)
