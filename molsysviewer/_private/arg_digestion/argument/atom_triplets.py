from ...exceptions import ArgumentError
from .._group_indices import digest_fixed_size_index_groups


def digest_atom_triplets(atom_triplets, caller=None):
    """Digest the atom triplets defining triangle faces.

    Each entry must hold exactly three atom indices (non-negative integers).
    ``None`` means the shape is defined by explicit vertices instead.
    """
    if atom_triplets is None:
        return None
    return digest_fixed_size_index_groups(atom_triplets, 3, "atom_triplets", caller=caller)
