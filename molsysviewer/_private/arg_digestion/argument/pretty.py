from ...exceptions import ArgumentError


def digest_pretty(pretty, caller=None):
    if isinstance(pretty, bool):
        return pretty
    raise ArgumentError("pretty", value=pretty, caller=caller, message=None)
