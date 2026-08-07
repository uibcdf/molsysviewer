import numpy as np
from molsysviewer._pyunitwizard import puw
from ...exceptions import ArgumentError

# `width` is a physical length almost everywhere in this library (shapes, boxes),
# but an iframe attribute is CSS: "100%", "480px". Same name, different domain,
# so the caller decides which one is being asked for.
_CSS_WIDTH_CALLERS = {
    "molsysviewer.tools.embed.embed_iframe",
    "molsysviewer.tools.embed_iframe",
}


def digest_width(width, caller=None):

    if caller in _CSS_WIDTH_CALLERS:
        if isinstance(width, str) and width.strip():
            return width.strip()
        if isinstance(width, int) and not isinstance(width, bool):
            return f"{width}px"
        raise ArgumentError('width', value=width, caller=caller,
                            message="Invalid width format. Expected a CSS length "
                                    "(e.g. '100%', '480px') or a number of pixels.")

    if isinstance(width, bool):
        raise ArgumentError('width', value=width, caller=caller, message=None)
    if isinstance(width, (int, float)):
        return float(width)
    if puw.is_quantity(width):
        if puw.check(width, dimensionality={'[L]':1}):
            return puw.standardize(width)

    raise ArgumentError('width', value=width, caller=caller, message=None)

