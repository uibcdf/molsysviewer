from ...exceptions import ArgumentError
from .._group_indices import digest_fixed_size_index_groups


def digest_atom_quads(atom_quads, caller=None):
    """Digest the atom quadruplets defining tetrahedra.

    Each entry must hold exactly four atom indices (non-negative integers).
    ``None`` means the shape is defined by explicit coordinates instead.
    """
    if atom_quads is None:
        return None
    return digest_fixed_size_index_groups(atom_quads, 4, "atom_quads", caller=caller)
