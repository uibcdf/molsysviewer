from ...exceptions import ArgumentError


def digest_scalars(scalars, caller=None):
    if scalars is None:
        return None
    if isinstance(scalars, (list, tuple)):
        if all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in scalars):
            return [float(item) for item in scalars]
    raise ArgumentError("scalars", value=scalars, caller=caller, message=None)
