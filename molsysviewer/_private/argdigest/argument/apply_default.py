from ...exceptions import ArgumentError


def digest_apply_default(apply_default, caller=None):
    if isinstance(apply_default, bool):
        return apply_default
    raise ArgumentError("apply_default", value=apply_default, caller=caller, message=None)
