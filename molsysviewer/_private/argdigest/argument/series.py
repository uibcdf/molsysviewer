"""`series` is the per-frame scalar data a trajectory plot draws.

Three shapes are accepted, and all three are in the public docstring: one sequence, a
`{label: sequence}` mapping, or a list of sequences.

What is *not* checked here is that the series have equal length. That rule needs the
number of frames, which `_normalize_series` establishes while flattening the three shapes
into one — checking it here would mean flattening twice, and the second copy would be the
one that ages.

The shape check still earns its place: passing a scalar, or a DataFrame, reaches
`_normalize_series` and fails inside it with a message about the normalised form rather
than about what was passed.
"""

from collections.abc import Mapping, Sequence

from molsysviewer._private.exceptions import ArgumentError


def digest_series(series, caller=None):
    if isinstance(series, Mapping):
        if not series:
            raise ArgumentError("series", value=series, caller=caller,
                                message="a plot of no series draws nothing")
        return series
    if isinstance(series, Sequence) and not isinstance(series, (str, bytes)):
        if not series:
            raise ArgumentError("series", value=series, caller=caller,
                                message="a plot of no series draws nothing")
        return series
    if hasattr(series, "__len__") and hasattr(series, "__getitem__"):
        return series  # a numpy array or anything else that indexes like one
    raise ArgumentError(
        "series",
        value=series,
        caller=caller,
        message="expected a sequence, a {label: sequence} mapping, or a list of sequences",
    )
