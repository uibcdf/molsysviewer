from ...exceptions import ArgumentError


def digest_near(near, caller=None):
    """Digest the near-clip radius, a percentage of the scene radius.

    The upper bound is 99 rather than 100: clipping the whole scene away from the
    front would leave nothing to draw.
    """
    if near is None:
        return None

    if isinstance(near, bool):
        raise ArgumentError("near", value=near, caller=caller, message=None)

    if isinstance(near, (int, float)):
        value = float(near)
        if 0.0 <= value <= 99.0:
            return value

    raise ArgumentError(
        "near",
        value=near,
        caller=caller,
        message=" The near-clip radius is a percentage between 0 and 99.",
    )
