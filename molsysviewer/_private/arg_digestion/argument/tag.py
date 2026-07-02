from molsysviewer._private.exceptions import ArgumentError


def digest_tag(tag, caller=None):
    if tag is None:
        return None
    if isinstance(tag, str):
        return tag
    # Shapes accept a batch tag: a list/tuple of tag strings (one per object).
    if isinstance(tag, (list, tuple)) and all(isinstance(t, str) for t in tag):
        return list(tag)
    raise ArgumentError("tag", value=tag, caller=caller, message=None)
