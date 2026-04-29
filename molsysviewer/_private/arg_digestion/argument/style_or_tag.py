from ...exceptions import ArgumentError


def digest_style_or_tag(style_or_tag, caller=None):
    if style_or_tag is None:
        return None

    from ....styles import Style

    if isinstance(style_or_tag, (Style, str)):
        return style_or_tag

    raise ArgumentError("style_or_tag", value=style_or_tag, caller=caller, message=None)
