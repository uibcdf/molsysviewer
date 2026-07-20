from ...exceptions import ArgumentError


def digest_color_component(color_component, caller=None):
    """Digest the vector component driving "component" colouring: 0, 1 or 2 (x, y, z)."""
    if isinstance(color_component, bool):
        raise ArgumentError("color_component", value=color_component, caller=caller, message=None)

    if isinstance(color_component, int) and color_component in (0, 1, 2):
        return color_component

    raise ArgumentError(
        "color_component",
        value=color_component,
        caller=caller,
        message=" The component must be 0, 1 or 2 (x, y or z).",
    )
