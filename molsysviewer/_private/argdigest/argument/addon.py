from ...exceptions import ArgumentError


def digest_addon(addon, caller=None):
    if isinstance(addon, str) and addon.strip():
        return addon.strip()
    raise ArgumentError("addon", value=addon, caller=caller, message=None)
