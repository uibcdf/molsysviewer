from ...exceptions import ArgumentError


def digest_discover_addons(discover_addons, caller=None):
    if isinstance(discover_addons, bool):
        return discover_addons
    raise ArgumentError("discover_addons", value=discover_addons, caller=caller)
