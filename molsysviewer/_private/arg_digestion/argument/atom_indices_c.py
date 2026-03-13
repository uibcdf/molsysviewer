from .atom_indices import digest_atom_indices


def digest_atom_indices_c(atom_indices_c, caller=None):
    return digest_atom_indices(atom_indices_c, caller=caller)
