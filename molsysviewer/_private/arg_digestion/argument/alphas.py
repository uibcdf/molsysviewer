from ...exceptions import ArgumentError


def digest_alphas(alphas, caller=None):
    if alphas is None:
        return None
    if isinstance(alphas, (int, float)) and not isinstance(alphas, bool):
        return float(alphas)
    if isinstance(alphas, (list, tuple)):
        if all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in alphas):
            return [float(item) for item in alphas]
    raise ArgumentError("alphas", value=alphas, caller=caller, message=None)
