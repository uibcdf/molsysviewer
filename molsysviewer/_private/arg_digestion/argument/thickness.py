from .._quantity import digest_length_quantity


def digest_thickness(thickness, caller=None):
    if thickness is None:
        return None
    return digest_length_quantity(thickness, "thickness", caller=caller)
