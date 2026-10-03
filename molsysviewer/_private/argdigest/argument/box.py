import numpy as np

from molsysviewer._pyunitwizard import puw

from ...exceptions import ArgumentError


def _box_values(box):
    """Validate a unit-bearing row-vector basis at the Viewer boundary."""
    if not puw.is_quantity(box):
        raise ValueError("Box vectors require an explicit length unit.")
    raw = np.asarray(puw.get_value(box, to_unit="nm"))
    if raw.dtype.kind not in "iuf":
        raise ValueError("Box vectors must contain real numbers.")
    values = np.asarray(raw, dtype=np.float64)
    if values.ndim == 2:
        values = values[None, :, :]
    if values.ndim != 3 or values.shape[1:] != (3, 3) or not len(values):
        raise ValueError("Box must have shape (3, 3) or (structures, 3, 3).")
    if not np.isfinite(values).all():
        raise ValueError("Box vectors must be finite.")
    # Check the relative basis, independent of units or overall cell size.
    lengths = np.linalg.norm(values, axis=2)
    if np.any(lengths <= 0) or not np.isfinite(lengths).all():
        raise ValueError("Box vectors must have nonzero finite lengths.")
    determinants = np.linalg.det(values / lengths[:, :, None])
    if np.any(determinants <= 1e-12):
        raise ValueError("Box vectors must form a nondegenerate right-handed basis.")
    return values


def digest_box(box, caller=None):
    if box is None:
        return None
    try:
        return puw.quantity(_box_values(box), "nm")
    except Exception as exc:
        raise ArgumentError("box", caller=caller, message=str(exc)) from exc
