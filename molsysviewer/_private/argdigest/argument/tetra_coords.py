from .._quantity import digest_length_quantity


def digest_tetra_coords(tetra_coords, caller=None):
    if tetra_coords is None:
        return None
    return digest_length_quantity(tetra_coords, "tetra_coords", caller=caller)
