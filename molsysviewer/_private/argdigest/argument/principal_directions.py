from ...exceptions import ArgumentError


def digest_principal_directions(principal_directions, caller=None):
    if principal_directions is None:
        return None
    if not isinstance(principal_directions, (list, tuple)):
        raise ArgumentError("principal_directions", value=principal_directions, caller=caller, message=None)
    normalized = []
    for item in principal_directions:
        if not isinstance(item, (list, tuple)) or len(item) != 3:
            raise ArgumentError("principal_directions", value=principal_directions, caller=caller, message=None)
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in item):
            raise ArgumentError("principal_directions", value=principal_directions, caller=caller, message=None)
        normalized.append([float(value) for value in item])
    return normalized
