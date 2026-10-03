from .._quantity import digest_length_quantity


def digest_offset_threshold(offset_threshold, caller=None):
    if offset_threshold is None:
        return None
    return digest_length_quantity(offset_threshold, "offset_threshold", caller)
