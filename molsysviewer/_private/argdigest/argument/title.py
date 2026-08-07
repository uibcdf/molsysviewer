from ...exceptions import ArgumentError


def digest_title(title, caller=None):
    if isinstance(title, str):
        return title
    raise ArgumentError("title", value=title, caller=caller, message=None)
