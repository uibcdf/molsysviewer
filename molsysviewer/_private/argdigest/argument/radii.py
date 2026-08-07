from .._quantity import digest_length_quantity


def digest_radii(radii, caller=None):
    if radii is None:
        return None
    return digest_length_quantity(radii, "radii", caller=caller)
