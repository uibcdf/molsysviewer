"""`point` is a location in the scene, in units of length.

It accepts what the public docstrings promise, which is more than a quantity:

- a PyUnitWizard quantity, of any length unit;
- **a plain `[x, y, z]` list, read as nanometres** — the spelling
  `scene.add_section` documents and `scene-object-panel-bridge.py` uses;
- `"centroid:<tag>"`, resolved later against the scene by the code that knows which
  objects exist.

The plain-list case was missing and the failure was not a refusal: `puw.get_value_and_unit`
raised `NotImplementedFormError` from inside PyUnitWizard, naming neither `point` nor the
call. It went unnoticed because every caller that could have hit it was undecorated —
`add_section` acquired `@digest` in the gate 9 scene slice, and this surfaced immediately.

Nanometres are the default because they are the scene's own unit, so a bare list means
what the rest of the library means by a bare number. Anything with a unit keeps it.
"""

import numpy as np

from molsysviewer._pyunitwizard import puw

from ...exceptions import ArgumentError

#: The unit a bare sequence is understood in. The scene's own unit, so a caller who omits
#: it gets what the surrounding code already assumes.
IMPLICIT_UNIT = "nm"


def digest_point(point, caller=None):

    if point is None:
        return None

    if isinstance(point, str):
        # A scene reference such as `"centroid:<tag>"`.
        return point

    if not puw.is_quantity(point):
        try:
            point = puw.quantity(np.asarray(point, dtype=np.float64), IMPLICIT_UNIT)
        except (TypeError, ValueError):
            raise ArgumentError('point', value=point, caller=caller, message=None) from None

    value, unit = puw.get_value_and_unit(point)

    if not puw.check(unit, dimensionality={'[L]': 1}):
        raise ArgumentError('point', value=point, caller=caller, message=None)

    if not isinstance(value, np.ndarray):
        value = np.array(value)

    value = value.astype(np.float64)
    shape = value.shape

    if len(shape) == 1:
        if shape[0] == 3:
            return puw.quantity(value[np.newaxis, :], unit, standardized=True)
    elif len(shape) == 2:
        if shape[1] == 3:
            return puw.quantity(value, unit, standardized=True)

    raise ArgumentError('point', value=point, caller=caller, message=None)
