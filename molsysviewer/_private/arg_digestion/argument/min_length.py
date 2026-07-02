from .._quantity import digest_length_quantity


def digest_min_length(min_length, caller=None):
    if min_length is None:
        return None
    return digest_length_quantity(min_length, "min_length", caller=caller)
