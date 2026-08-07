from ...exceptions import ArgumentError


def digest_grid(grid, caller=None):
    if grid is None:
        return None
    if not isinstance(grid, dict):
        raise ArgumentError("grid", value=grid, caller=caller, message=None)

    allowed = {"resolution", "radius_offset", "smoothness"}
    output = {}
    for key, value in grid.items():
        if key not in allowed:
            raise ArgumentError("grid", value=grid, caller=caller, message=None)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ArgumentError("grid", value=grid, caller=caller, message=None)
        output[key] = float(value)
    return output
