from ...exceptions import ArgumentError


def digest_label_style(label_style, caller=None):
    if label_style is None:
        return None
    if isinstance(label_style, dict):
        return label_style
    raise ArgumentError("label_style", value=label_style, caller=caller, message=None)
