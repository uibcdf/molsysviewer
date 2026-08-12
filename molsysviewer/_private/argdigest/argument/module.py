"""`module` is the add-on module to register, by name or already imported.

Both forms are accepted because both are useful: a string is what a user types
(`register_module("molsysviewer_topomt")`) and a module object is what a toolkit passes
when it registers itself from its own `__init__`.

Nothing is imported here. Whether the name resolves, and whether what it resolves to
exposes an `AddonSpec`, is `register_module`'s job — it already reports both, and
importing twice to check would run an add-on's import side effects before deciding to.
"""

from types import ModuleType

from molsysviewer._private.exceptions import ArgumentError


def digest_module(module, caller=None):
    if isinstance(module, (str, ModuleType)):
        return module
    raise ArgumentError(
        "module",
        value=module,
        caller=caller,
        message="expected a module name or an imported module",
    )
