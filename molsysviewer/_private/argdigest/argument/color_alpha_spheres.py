"""Deferred colour import.

This digester needs `molsysviewer.colors`, and `colors.py` is itself decorated. The
digester package is loaded eagerly at decoration time, so a module-level import here
would land while `colors` is still initialising. The import is inside the function
instead, which costs one dict lookup per call.
"""

from ...exceptions import ArgumentError


def digest_color_alpha_spheres(color_alpha_spheres, caller=None):
    """Digest the ``color_alpha_spheres`` colour, normalized to a packed integer.

    Accepts any colour form the viewer understands (packed int, ``"#rrggbb"``,
    a name, an RGB(A) triplet). ``None`` keeps the shape's own default.
    """
    from molsysviewer.colors import normalize_color  # deferred: see module note
    if color_alpha_spheres is None:
        return None

    try:
        return normalize_color(color_alpha_spheres)
    except Exception as exc:
        raise ArgumentError("color_alpha_spheres", value=color_alpha_spheres, caller=caller, message=None) from exc
