from .._quantity import digest_length_quantity


def digest_max_length(max_length, caller=None):
    if max_length is None:
        return None
    return digest_length_quantity(max_length, "max_length", caller=caller)
