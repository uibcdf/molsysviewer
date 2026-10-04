from ...exceptions import ArgumentError

_COLOR_SCALARS = (int, str)


def digest_colors(colors, caller=None):
    if caller == "molsysviewer.colors.normalize_colors":
        from molsysviewer.colors import _normalize_colors

        try:
            return _normalize_colors(colors)
        except (TypeError, ValueError) as exc:
            raise ArgumentError("colors", value=colors, caller=caller) from exc
    if colors is None:
        return None
    if isinstance(colors, _COLOR_SCALARS) and not isinstance(colors, bool):
        return colors
    if isinstance(colors, (list, tuple)):
        if all(isinstance(item, _COLOR_SCALARS) and not isinstance(item, bool) for item in colors):
            return list(colors)
    raise ArgumentError("colors", value=colors, caller=caller, message=None)
