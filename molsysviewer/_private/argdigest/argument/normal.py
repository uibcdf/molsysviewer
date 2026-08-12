"""`normal` is the direction a clipping plane faces.

**It is not a position, and must not be digested as one.** An earlier draft delegated to
`digest_point`, which reads its input as a length in nanometres and hands it to
PyUnitWizard — reasonable for `point`, wrong for a direction, which has no units at all.
The result was a `NotImplementedFormError` from inside a unit conversion on a call that
had always worked.

Accepted, per `add_section`'s own documentation:

- any non-zero 3-vector, which the caller normalises;
- `"toward:<tag>"` and `"mouth:<tag>"`, resolved later against the scene.

The zero vector is refused here and nowhere else. It defines no plane, and Mol\\* does not
complain: it clips nothing, so the user sees an unchanged scene and no error, which is the
most expensive way to be told that an argument was wrong.
"""

import numpy as np

from molsysviewer._private.exceptions import ArgumentError


def digest_normal(normal, caller=None):
    if normal is None:
        return None

    if isinstance(normal, str):
        # A scene reference; the tag is resolved when the section is built, by the code
        # that knows which scene objects exist.
        return normal

    try:
        vector = np.asarray(normal, dtype=float)
    except (TypeError, ValueError):
        raise ArgumentError("normal", value=normal, caller=caller,
                            message="expected a 3-vector or a 'toward:<tag>' reference") from None

    if vector.shape != (3,):
        raise ArgumentError("normal", value=normal, caller=caller,
                            message="a plane normal has three components")
    if not np.isfinite(vector).all():
        raise ArgumentError("normal", value=normal, caller=caller,
                            message="a plane normal cannot contain nan or inf")
    if float(np.linalg.norm(vector)) == 0.0:
        raise ArgumentError(
            "normal",
            value=normal,
            caller=caller,
            message="the zero vector defines no plane; nothing would be clipped",
        )
    return normal
