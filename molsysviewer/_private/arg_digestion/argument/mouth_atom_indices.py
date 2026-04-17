from ...exceptions import ArgumentError


def digest_mouth_atom_indices(mouth_atom_indices, caller=None):
    if mouth_atom_indices is None:
        return None
    if not isinstance(mouth_atom_indices, (list, tuple)):
        raise ArgumentError("mouth_atom_indices", value=mouth_atom_indices, caller=caller, message=None)

    if all(isinstance(item, int) and not isinstance(item, bool) for item in mouth_atom_indices):
        return [int(item) for item in mouth_atom_indices]

    if all(isinstance(item, (list, tuple)) for item in mouth_atom_indices):
        normalized = []
        for item in mouth_atom_indices:
            if not all(isinstance(index, int) and not isinstance(index, bool) for index in item):
                raise ArgumentError("mouth_atom_indices", value=mouth_atom_indices, caller=caller, message=None)
            normalized.append([int(index) for index in item])
        return normalized

    raise ArgumentError("mouth_atom_indices", value=mouth_atom_indices, caller=caller, message=None)
