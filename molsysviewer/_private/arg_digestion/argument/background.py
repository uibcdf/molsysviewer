from ...exceptions import ArgumentError


def digest_background(background, caller=None):
    if isinstance(background, str) and background in {"white", "dark", "transparent", "current"}:
        return background
    raise ArgumentError("background", value=background, caller=caller, message=None)
