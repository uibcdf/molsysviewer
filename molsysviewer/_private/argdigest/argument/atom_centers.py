from .._quantity import digest_length_quantity


def digest_atom_centers(atom_centers, caller=None):
    if atom_centers is None:
        return None
    return digest_length_quantity(atom_centers, "atom_centers", caller=caller)
