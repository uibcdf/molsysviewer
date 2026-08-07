from ...exceptions import ArgumentError


def digest_source(source, caller=None):
    if isinstance(source, str):
        return source
    raise ArgumentError("source", value=source, caller=caller, message=None)
