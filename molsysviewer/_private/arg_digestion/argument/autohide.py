from ...exceptions import ArgumentError


def digest_autohide(autohide, caller=None):
    if autohide is None or isinstance(autohide, bool):
        return autohide
    raise ArgumentError("autohide", value=autohide, caller=caller, message=None)
