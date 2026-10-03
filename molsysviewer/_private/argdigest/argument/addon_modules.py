from ...exceptions import ArgumentError


def digest_addon_modules(addon_modules, caller=None):
    if addon_modules is None:
        return None
    if isinstance(addon_modules, (list, tuple)) and all(isinstance(item, str) for item in addon_modules):
        return list(addon_modules)
    raise ArgumentError("addon_modules", value=addon_modules, caller=caller)
