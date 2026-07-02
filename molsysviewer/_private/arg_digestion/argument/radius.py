from .._quantity import digest_length_quantity


def digest_radius(radius, caller=None):
    return digest_length_quantity(radius, "radius", caller=caller)
