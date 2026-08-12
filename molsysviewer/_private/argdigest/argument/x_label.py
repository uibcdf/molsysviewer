"""`x_label` labels the x-axis of a trajectory plot.

A string, or `None` to leave the axis unlabelled. Declared rather than left undeclared so
that a caller passing a number — a column index, say — is told which argument was wrong
instead of seeing it stringified into the plot.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_x_label(x_label, caller=None):
    if x_label is None or isinstance(x_label, str):
        return x_label
    raise ArgumentError("x_label", value=x_label, caller=caller,
                        message="an axis label is a string")
