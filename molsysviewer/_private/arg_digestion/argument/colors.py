from ...exceptions import ArgumentError


_COLOR_SCALARS = (int, str)


def digest_colors(colors, caller=None):
    if colors is None:
        return None
    if isinstance(colors, _COLOR_SCALARS) and not isinstance(colors, bool):
        return colors
    if isinstance(colors, (list, tuple)):
        if all(isinstance(item, _COLOR_SCALARS) and not isinstance(item, bool) for item in colors):
            return list(colors)
    raise ArgumentError("colors", value=colors, caller=caller, message=None)
