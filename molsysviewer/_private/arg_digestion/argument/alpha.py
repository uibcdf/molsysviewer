from ...exceptions import ArgumentError


def digest_alpha(alpha, caller=None):
    if alpha is None:
        return None
    if isinstance(alpha, (int, float)) and not isinstance(alpha, bool):
        return float(alpha)
    raise ArgumentError("alpha", value=alpha, caller=caller, message=None)
