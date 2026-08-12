"""`easing` is the interpolation curve between two movie keyframes.

The closed set is Mol*'s, and it is read from the movie module rather than restated, so a
curve added there cannot leave this file behind. The rule already existed in
`add_keyframe` as a bare `ValueError`; moving it here gives it a caller and applies it to
every entry point that takes one.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_easing(easing, caller=None):
    if easing is None:
        return None
    from molsysviewer.viewer.movie import _EASING_VALUES

    if easing in _EASING_VALUES:
        return easing
    raise ArgumentError(
        "easing",
        value=easing,
        caller=caller,
        message=f"expected one of {', '.join(sorted(_EASING_VALUES))}",
    )
