"""`n_keyframes` is how finely a generated camera orbit is sampled.

At least two: one keyframe is a still, and the orbit's interpolation needs a start and an
end. The default is 36 — one every ten degrees — and there is no upper bound, because a
smoother orbit is a choice whose cost the caller pays in file size.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_n_keyframes(n_keyframes, caller=None):
    if isinstance(n_keyframes, bool) or not isinstance(n_keyframes, int):
        raise ArgumentError("n_keyframes", value=n_keyframes, caller=caller,
                            message="expected a whole number of keyframes")
    if n_keyframes < 2:
        raise ArgumentError(
            "n_keyframes",
            value=n_keyframes,
            caller=caller,
            message="an orbit needs at least a start and an end",
        )
    return n_keyframes
