from .._quantity import digest_length_quantity


def digest_atom_radius(atom_radius, caller=None):
    if atom_radius is None:
        return None
    return digest_length_quantity(atom_radius, "atom_radius", caller=caller)
