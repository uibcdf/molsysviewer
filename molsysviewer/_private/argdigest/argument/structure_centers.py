from .._quantity import digest_length_quantity


def digest_structure_centers(structure_centers, caller=None):
    if structure_centers is None:
        return None
    return digest_length_quantity(structure_centers, "structure_centers", caller=caller)
