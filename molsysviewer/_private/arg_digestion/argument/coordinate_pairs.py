from .._quantity import digest_length_quantity


def digest_coordinate_pairs(coordinate_pairs, caller=None):
    if coordinate_pairs is None:
        return None
    return digest_length_quantity(coordinate_pairs, "coordinate_pairs", caller=caller)
