from ...exceptions import ArgumentError


_VERTICAL = {"top", "bottom"}
_HORIZONTAL = {"left", "right"}


def _normalize_position(value):
    if value is None:
        return None
    if isinstance(value, str):
        tokens = value.replace(",", " ").split()
    elif isinstance(value, (list, tuple)):
        tokens = list(value)
    else:
        raise TypeError
    if len(tokens) != 2 or not all(isinstance(token, str) for token in tokens):
        raise TypeError
    vertical = next((token for token in tokens if token in _VERTICAL), None)
    horizontal = next((token for token in tokens if token in _HORIZONTAL), None)
    if vertical is None or horizontal is None:
        raise TypeError
    return [vertical, horizontal]


def digest_position_fullscreen(position_fullscreen, caller=None):
    try:
        return _normalize_position(position_fullscreen)
    except Exception:
        raise ArgumentError("position_fullscreen", value=position_fullscreen, caller=caller, message=None) from None
