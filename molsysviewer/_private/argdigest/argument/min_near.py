from ...exceptions import ArgumentError


def digest_min_near(min_near, caller=None):
    """Digest the minimum near-plane distance, in scene units.

    It is a distance, so it cannot be negative. Unlike `near` and `far` it is not a
    percentage and has no upper bound.
    """
    if min_near is None:
        return None

    if isinstance(min_near, bool):
        raise ArgumentError("min_near", value=min_near, caller=caller, message=None)

    if isinstance(min_near, (int, float)):
        value = float(min_near)
        if value >= 0.0:
            return value

    raise ArgumentError(
        "min_near",
        value=min_near,
        caller=caller,
        message=" The minimum near-plane distance must be a non-negative number.",
    )
