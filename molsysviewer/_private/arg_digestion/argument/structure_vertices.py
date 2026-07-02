from .._quantity import digest_length_quantity


def digest_structure_vertices(structure_vertices, caller=None):
    if structure_vertices is None:
        return None
    return digest_length_quantity(structure_vertices, "structure_vertices", caller=caller)
