import numpy as np

from ...exceptions import ArgumentError


def digest_structures_atom_indices(structures_atom_indices, caller=None):
    """Digest per-structure atom indices: one list of indices per structure.

    ``None`` means the shape does not follow the trajectory. A structure may
    carry an empty list, which hides the shape on that structure.
    """
    if structures_atom_indices is None:
        return None

    if isinstance(structures_atom_indices, np.ndarray):
        structures_atom_indices = structures_atom_indices.tolist()

    if not isinstance(structures_atom_indices, (list, tuple)):
        raise ArgumentError("structures_atom_indices", value=structures_atom_indices, caller=caller, message=None)

    out = []
    for per_structure in structures_atom_indices:
        if per_structure is None:
            out.append(None)
            continue
        if isinstance(per_structure, np.ndarray):
            per_structure = per_structure.tolist()
        if not isinstance(per_structure, (list, tuple)):
            raise ArgumentError("structures_atom_indices", value=structures_atom_indices, caller=caller, message=None)
        indices = []
        for index in per_structure:
            if isinstance(index, bool) or not isinstance(index, (int, np.integer)) or int(index) < 0:
                raise ArgumentError("structures_atom_indices", value=structures_atom_indices, caller=caller, message=None)
            indices.append(int(index))
        out.append(indices)
    return out
