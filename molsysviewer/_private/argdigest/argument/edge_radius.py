from .._quantity import digest_length_quantity


def digest_edge_radius(edge_radius, caller=None):
    if edge_radius is None:
        return None
    return digest_length_quantity(edge_radius, "edge_radius", caller=caller)
