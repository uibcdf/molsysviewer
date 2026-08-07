from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_molstar_color_theme(molstar_color_theme, caller=None):
    if molstar_color_theme is None:
        return None
    if isinstance(molstar_color_theme, str):
        return molstar_color_theme
    if isinstance(molstar_color_theme, Mapping):
        name = molstar_color_theme.get("name")
        params = molstar_color_theme.get("params", {})
        if not isinstance(name, str):
            raise ArgumentError(
                "molstar_color_theme",
                value=molstar_color_theme,
                caller=caller,
                message="molstar_color_theme dictionaries require a string 'name'.",
            )
        if not isinstance(params, Mapping):
            raise ArgumentError(
                "molstar_color_theme",
                value=molstar_color_theme,
                caller=caller,
                message="molstar_color_theme dictionaries require 'params' to be a mapping.",
            )
        return {"name": name, "params": dict(params)}
    raise ArgumentError("molstar_color_theme", value=molstar_color_theme, caller=caller, message=None)
