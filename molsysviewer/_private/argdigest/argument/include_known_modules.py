"""`include_known_modules` widens discovery to the MolSysSuite siblings by name.

A strict boolean. It controls whether `KNOWN_ADDON_MODULES` is tried in addition to entry
points, so a truthy value would silently import four sibling packages a caller did not ask
for.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_include_known_modules(include_known_modules, caller=None):
    if isinstance(include_known_modules, bool):
        return include_known_modules
    raise ArgumentError("include_known_modules", value=include_known_modules, caller=caller,
                        message="expected True or False")
