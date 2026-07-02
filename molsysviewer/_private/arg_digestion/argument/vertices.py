from .._quantity import digest_length_quantity


def digest_vertices(vertices, caller=None):
    if vertices is None:
        return None
    return digest_length_quantity(vertices, "vertices", caller=caller)
