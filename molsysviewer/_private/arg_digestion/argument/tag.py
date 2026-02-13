from molsysviewer._private.exceptions import ArgumentError


def digest_tag(tag, caller=None):
    if tag is None:
        return None
    if isinstance(tag, str):
        return tag
    raise ArgumentError("tag", value=tag, caller=caller, message=None)
