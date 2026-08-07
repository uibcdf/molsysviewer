from .._quantity import digest_length_quantity


def digest_origins(origins, caller=None):
    if origins is None:
        return None
    return digest_length_quantity(origins, "origins", caller=caller)
