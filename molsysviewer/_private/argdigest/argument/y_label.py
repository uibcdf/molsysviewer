"""`y_label` labels the y-axis of a trajectory plot.

A string, or `None` to leave the axis unlabelled. Declared rather than left undeclared so
that a caller passing a number — a column index, say — is told which argument was wrong
instead of seeing it stringified into the plot.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_y_label(y_label, caller=None):
    if y_label is None or isinstance(y_label, str):
        return y_label
    raise ArgumentError("y_label", value=y_label, caller=caller,
                        message="an axis label is a string")
