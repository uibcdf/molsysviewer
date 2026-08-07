from molsysviewer.colors import normalize_color

from ...exceptions import ArgumentError


def digest_color_atoms(color_atoms, caller=None):
    """Digest the ``color_atoms`` colour, normalized to a packed integer.

    Accepts any colour form the viewer understands (packed int, ``"#rrggbb"``,
    a name, an RGB(A) triplet). ``None`` keeps the shape's own default.
    """
    if color_atoms is None:
        return None

    try:
        return normalize_color(color_atoms)
    except Exception as exc:
        raise ArgumentError("color_atoms", value=color_atoms, caller=caller, message=None) from exc
