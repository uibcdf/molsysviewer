from .._quantity import digest_length_quantity


def digest_normal_length(normal_length, caller=None):
    if normal_length is None:
        return None
    return digest_length_quantity(normal_length, "normal_length", caller=caller)
