from molsysviewer.colors import normalize_color

from ...exceptions import ArgumentError


def digest_color_alpha_spheres(color_alpha_spheres, caller=None):
    """Digest the ``color_alpha_spheres`` colour, normalized to a packed integer.

    Accepts any colour form the viewer understands (packed int, ``"#rrggbb"``,
    a name, an RGB(A) triplet). ``None`` keeps the shape's own default.
    """
    if color_alpha_spheres is None:
        return None

    try:
        return normalize_color(color_alpha_spheres)
    except Exception as exc:
        raise ArgumentError("color_alpha_spheres", value=color_alpha_spheres, caller=caller, message=None) from exc
