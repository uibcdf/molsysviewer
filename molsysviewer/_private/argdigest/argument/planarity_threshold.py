from .._quantity import digest_length_quantity


def digest_planarity_threshold(planarity_threshold, caller=None):
    if planarity_threshold is None:
        return None
    return digest_length_quantity(planarity_threshold, "planarity_threshold", caller)
