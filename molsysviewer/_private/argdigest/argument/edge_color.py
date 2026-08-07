from molsysviewer.colors import normalize_color

from ...exceptions import ArgumentError


def digest_edge_color(edge_color, caller=None):
    """Digest the ``edge_color`` colour, normalized to a packed integer.

    Accepts any colour form the viewer understands (packed int, ``"#rrggbb"``,
    a name, an RGB(A) triplet). ``None`` keeps the shape's own default.
    """
    if edge_color is None:
        return None

    try:
        return normalize_color(edge_color)
    except Exception as exc:
        raise ArgumentError("edge_color", value=edge_color, caller=caller, message=None) from exc
