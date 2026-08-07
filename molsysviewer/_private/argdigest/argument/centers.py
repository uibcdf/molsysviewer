from .._quantity import digest_length_quantity


def digest_centers(centers, caller=None):
    if centers is None:
        return None
    return digest_length_quantity(centers, "centers", caller=caller)
