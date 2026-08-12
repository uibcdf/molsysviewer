from ...exceptions import ArgumentError

#: `register` is handed the add-on itself; every other caller names one that is already
#: registered. The same split as `scheme`: digesting a definition against the registry of
#: known names refuses every add-on at the moment it is registered.
_ADDON_DEFINING_CALLERS = frozenset({
    "molsysviewer.addons.register",
    "molsysviewer.addons.GlobalAddonsRegistry.register",
})


def digest_addon(addon, caller=None):
    if caller in _ADDON_DEFINING_CALLERS:
        # An AddonSpec. What makes it a *valid* one -- the version requirement, the panel
        # entries, the lifecycle hooks -- is the registry's own business, and `register`
        # already reports each with its own message.
        return addon
    if isinstance(addon, str) and addon.strip():
        return addon.strip()
    raise ArgumentError("addon", value=addon, caller=caller, message=None)
