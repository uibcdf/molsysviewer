"""Deferred colour import.

This digester needs `molsysviewer.colors`, and `colors.py` is itself decorated. The
digester package is loaded eagerly at decoration time, so a module-level import here
would land while `colors` is still initialising. The import is inside the function
instead, which costs one dict lookup per call.
"""
from molsysviewer._private.exceptions import ArgumentError
import numpy as np


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


#: `scene.set_background` takes a colour **or** a theme keyword, and the keywords are not
#: colours: `"light"` and `"dark"` select the built-in presets and take a different branch
#: of the method, sending `toggle_background` instead of `set_background_color`.
#: Normalising them would have to invent a hex value, which is precisely what the presets
#: exist to avoid.
_THEME_KEYWORDS = frozenset({"light", "dark"})
_THEME_ACCEPTING_CALLERS = frozenset({
    "molsysviewer.scene.set_background",
    "molsysviewer.scene.SceneManager.set_background",
})


def digest_color(color, caller=None):
    """Normalize a single colour, or a batch (sequence) of colours, to int(s)."""
    from molsysviewer.colors import normalize_color, normalize_colors  # deferred: see module note
    if color is None:
        return None
    if (caller in _THEME_ACCEPTING_CALLERS and isinstance(color, str)
            and color.strip().lower() in _THEME_KEYWORDS):
        return color.strip().lower()
    try:
        if isinstance(color, (list, tuple, np.ndarray)) and not _looks_like_single_rgb(color):
            return normalize_colors(list(color))
        return normalize_color(color)
    except Exception as exc:
        raise ArgumentError('color', value=color, caller=caller) from exc
