from ...exceptions import ArgumentError


def digest_color_map(color_map, caller=None):
    if color_map is None:
        return None
    if isinstance(color_map, str):
        return color_map
    if isinstance(color_map, (list, tuple)):
        if all(isinstance(item, int) and not isinstance(item, bool) for item in color_map):
            return list(color_map)
    raise ArgumentError("color_map", value=color_map, caller=caller, message=None)
