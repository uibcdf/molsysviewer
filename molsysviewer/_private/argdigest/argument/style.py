from ...exceptions import ArgumentError


def digest_style(style, caller=None):
    if style is None:
        return None

    from ....styles import Style

    if isinstance(style, Style):
        return style

    raise ArgumentError("style", value=style, caller=caller, message=None)
