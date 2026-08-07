from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_molstar_size_theme(molstar_size_theme, caller=None):
    if molstar_size_theme is None:
        return None
    if isinstance(molstar_size_theme, str):
        return molstar_size_theme
    if isinstance(molstar_size_theme, Mapping):
        name = molstar_size_theme.get("name")
        params = molstar_size_theme.get("params", {})
        if not isinstance(name, str):
            raise ArgumentError(
                "molstar_size_theme",
                value=molstar_size_theme,
                caller=caller,
                message="molstar_size_theme dictionaries require a string 'name'.",
            )
        if not isinstance(params, Mapping):
            raise ArgumentError(
                "molstar_size_theme",
                value=molstar_size_theme,
                caller=caller,
                message="molstar_size_theme dictionaries require 'params' to be a mapping.",
            )
        return {"name": name, "params": dict(params)}
    raise ArgumentError("molstar_size_theme", value=molstar_size_theme, caller=caller, message=None)
