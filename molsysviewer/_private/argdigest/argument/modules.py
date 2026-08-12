"""`modules` is the explicit list of add-on modules `discover` should try.

`None` means "use the default discovery routes" — entry points, and
`KNOWN_ADDON_MODULES` when `include_known_modules` is set. An **empty** sequence is a
different thing and is refused: it asks discovery to try nothing, succeeds, and reports no
add-ons, which is indistinguishable from a broken installation.

A bare string is refused too, because it would iterate character by character and try to
import `"m"`. That failure reports eleven import errors and never mentions the argument.
"""

from collections.abc import Sequence

from molsysviewer._private.exceptions import ArgumentError


def digest_modules(modules, caller=None):
    if modules is None:
        return None
    if isinstance(modules, str):
        raise ArgumentError("modules", value=modules, caller=caller,
                            message="expected a sequence of module names; for one, wrap it")
    if not isinstance(modules, Sequence):
        raise ArgumentError("modules", value=modules, caller=caller,
                            message="expected a sequence of module names")
    if not modules:
        raise ArgumentError(
            "modules",
            value=modules,
            caller=caller,
            message="discovering nothing succeeds and looks like a broken install",
        )
    for name in modules:
        if not isinstance(name, str):
            raise ArgumentError("modules", value=name, caller=caller,
                                message="a module name is a string")
    return list(modules)
