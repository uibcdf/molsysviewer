from molsysviewer.colors import normalize_color

from ...exceptions import ArgumentError


def digest_normal_color(normal_color, caller=None):
    """Digest the ``normal_color`` colour, normalized to a packed integer.

    Accepts any colour form the viewer understands (packed int, ``"#rrggbb"``,
    a name, an RGB(A) triplet). ``None`` keeps the shape's own default.
    """
    if normal_color is None:
        return None

    try:
        return normalize_color(normal_color)
    except Exception as exc:
        raise ArgumentError("normal_color", value=normal_color, caller=caller, message=None) from exc
