from ...exceptions import ArgumentError


def digest_drop_defaults(drop_defaults, caller=None):
    if isinstance(drop_defaults, bool):
        return drop_defaults
    raise ArgumentError("drop_defaults", value=drop_defaults, caller=caller)
