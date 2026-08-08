from ...exceptions import ArgumentError


def digest_far(far, caller=None):
    """Digest the far-clip depth, a percentage of the scene radius from the back.

    Zero disables far clipping, so the whole range up to 100 is meaningful here.
    """
    if far is None:
        return None

    if isinstance(far, bool):
        raise ArgumentError("far", value=far, caller=caller, message=None)

    if isinstance(far, (int, float)):
        value = float(far)
        if 0.0 <= value <= 100.0:
            return value

    raise ArgumentError(
        "far",
        value=far,
        caller=caller,
        message=" The far-clip depth is a percentage between 0 and 100.",
    )
