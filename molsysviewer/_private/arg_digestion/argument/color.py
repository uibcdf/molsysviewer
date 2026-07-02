from molsysviewer._private.exceptions import ArgumentError
import numpy as np
from molsysviewer.colors import normalize_color, normalize_colors


def _looks_like_single_rgb(color):
    """A flat length-3/4 numeric sequence in channel range is one RGB(A) colour.

    This disambiguates a single ``[r, g, b]`` from a batch of colour integers:
    channel values are ints in ``0..255`` or floats in ``0..1``; packed colour
    integers (e.g. ``0xFF0000``) fall outside that range and read as a batch.
    """
    if not isinstance(color, (list, tuple, np.ndarray)):
        return False
    seq = list(color)
    if len(seq) not in (3, 4):
        return False
    if any(isinstance(c, bool) or not isinstance(c, (int, float, np.number)) for c in seq):
        return False
    if all(isinstance(c, (int, np.integer)) and not isinstance(c, bool) for c in seq):
        return all(0 <= int(c) <= 255 for c in seq)
    return all(0.0 <= float(c) <= 1.0 for c in seq)


def digest_color(color, caller=None):
    """Normalize a single colour, or a batch (sequence) of colours, to int(s)."""
    if color is None:
        return None
    try:
        if isinstance(color, (list, tuple, np.ndarray)) and not _looks_like_single_rgb(color):
            return normalize_colors(list(color))
        return normalize_color(color)
    except Exception as exc:
        raise ArgumentError('color', value=color, caller=caller) from exc
