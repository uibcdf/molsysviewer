from ...exceptions import ArgumentError


def digest_style(style, caller=None):
    if caller and caller.startswith("molsysviewer.annotations."):
        if isinstance(style, dict):
            return style
        raise ArgumentError("style", value=style, caller=caller)
    if style is None:
        return None

    from ....styles import Style

    if isinstance(style, Style):
        return style

    raise ArgumentError("style", value=style, caller=caller, message=None)
