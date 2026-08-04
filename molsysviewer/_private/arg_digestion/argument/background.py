from ...exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

# An image is looked at as it was made; an exported page is read later, on a
# screen nobody has seen, inside somebody else's site. So the HTML export takes
# two answers a still image has no use for — follow the reader, or inherit the
# host — alongside the two fixed ones it shares with figures.
_HTML_EXPORT_CALLERS = {
    "molsysviewer.exports.html",
    "molsysviewer.exports.ExportManager.html",
    "molsysviewer.viewer.write_html",
    "molsysviewer.viewer.MolSysView.write_html",
}

_HTML_VALUES = {"auto", "transparent", "white", "dark"}
_IMAGE_VALUES = {"white", "dark", "transparent", "current"}


def digest_background(background, caller=None):
    caller = normalize_viewer_caller(caller)
    allowed = _HTML_VALUES if caller in _HTML_EXPORT_CALLERS else _IMAGE_VALUES

    if isinstance(background, str) and background in allowed:
        return background

    raise ArgumentError(
        "background",
        value=background,
        caller=caller,
        message=f"Expected one of {sorted(allowed)}.",
    )
