import numpy as np

from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw


def digest_values(values, caller=None):

    if caller == "molsysviewer.colors.normalize_colors":
        from molsysviewer.colors import _normalize_colors

        try:
            return _normalize_colors(values)
        except (TypeError, ValueError) as exc:
            raise ArgumentError("values", value=values, caller=caller) from exc
    if values is None:
        return values

    if puw.is_quantity(values):
        try:
            return puw.ensure_quantity(values, standardized=False, caller=caller)
        except Exception as exc:
            raise ArgumentError("values", value=values, caller=caller) from exc

    if isinstance(values, (list, tuple, range, np.ndarray)):
        return values

    raise ArgumentError("values", value=values, caller=caller, message=None)
