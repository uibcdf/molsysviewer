"""`camera` is a camera snapshot stored on a movie keyframe.

A mapping or `None`. Its *contents* are Mol*'s camera state, mirrored back from the
frontend by `view.get_camera_snapshot()`, and this deliberately does not inspect them:
the shape belongs to Mol*, and a check here would encode a version of it that the next
Mol* release could invalidate silently.

What it does catch is the mistake the argument invites — passing the view, or the camera
manager, instead of a snapshot taken from it.
"""

from collections.abc import Mapping

from molsysviewer._private.exceptions import ArgumentError


def digest_camera(camera, caller=None):
    if camera is None:
        return None
    if isinstance(camera, Mapping):
        return camera
    raise ArgumentError(
        "camera",
        value=camera,
        caller=caller,
        message="expected a snapshot dict from view.get_camera_snapshot()",
    )
