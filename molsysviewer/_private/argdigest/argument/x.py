"""`x` are the x-axis values of a trajectory plot.

`None` means frame indices `0..n-1`, which is what most callers want.

Length is not checked here — it must equal the number of frames, and that comes from
`series` after normalisation, which this digester does not see. `show` refuses the
mismatch and says both numbers. What is checked is that it is a sequence at all, since the
alternative is a `TypeError` from `float(v)` inside a comprehension.
"""

from collections.abc import Sequence

from molsysviewer._private.exceptions import ArgumentError


def digest_x(x, caller=None):
    if x is None:
        return None
    if isinstance(x, (str, bytes)) or not (
        isinstance(x, Sequence) or (hasattr(x, "__len__") and hasattr(x, "__getitem__"))
    ):
        raise ArgumentError("x", value=x, caller=caller,
                            message="expected a sequence of x-axis values")
    return x
