from ...exceptions import ArgumentError


def digest_include_popout(include_popout, caller=None):
    if isinstance(include_popout, bool):
        return include_popout
    raise ArgumentError("include_popout", value=include_popout, caller=caller, message=None)
