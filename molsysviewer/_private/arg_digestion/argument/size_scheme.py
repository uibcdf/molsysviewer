from ...exceptions import ArgumentError


def digest_size_scheme(size_scheme, caller=None):
    if size_scheme is None:
        return None
    if isinstance(size_scheme, str):
        return size_scheme
    raise ArgumentError("size_scheme", value=size_scheme, caller=caller, message=None)
