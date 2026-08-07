from ...exceptions import ArgumentError


def digest_kind(kind, caller=None):
    if kind is None or isinstance(kind, str):
        return kind
    raise ArgumentError("kind", value=kind, caller=caller, message=None)
