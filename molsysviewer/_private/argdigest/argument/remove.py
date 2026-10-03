from ...exceptions import ArgumentError


def digest_remove(remove, caller=None):
    if isinstance(remove, bool):
        return remove
    raise ArgumentError("remove", value=remove, caller=caller)
