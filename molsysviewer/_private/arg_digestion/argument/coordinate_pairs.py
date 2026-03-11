from ...exceptions import ArgumentError


def digest_coordinate_pairs(coordinate_pairs, caller=None):
    if coordinate_pairs is None:
        return None
    if not isinstance(coordinate_pairs, (list, tuple)):
        raise ArgumentError("coordinate_pairs", value=coordinate_pairs, caller=caller, message=None)
    normalized = []
    try:
        for pair in coordinate_pairs:
            if len(pair) != 2:
                raise ValueError
            start, end = pair
            if len(start) != 3 or len(end) != 3:
                raise ValueError
            normalized.append([
                [float(start[0]), float(start[1]), float(start[2])],
                [float(end[0]), float(end[1]), float(end[2])],
            ])
    except Exception:
        raise ArgumentError("coordinate_pairs", value=coordinate_pairs, caller=caller, message=None) from None
    return normalized
