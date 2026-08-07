import numpy as np

from ...exceptions import ArgumentError


def digest_normals(normals, caller=None):
    """Digest a sequence of 3D vectors, one per element.

    Returns a list of ``[x, y, z]`` floats. ``None`` means the shape does not
    use them. Non-finite components are rejected: they would produce degenerate
    geometry in the frontend.
    """
    if normals is None:
        return None

    value = normals
    if isinstance(value, np.ndarray):
        if value.ndim != 2 or value.shape[1] != 3:
            raise ArgumentError("normals", value=normals, caller=caller, message=None)
        value = value.tolist()

    if not isinstance(value, (list, tuple)) or len(value) == 0:
        raise ArgumentError("normals", value=normals, caller=caller, message=None)

    out = []
    for vector in value:
        if isinstance(vector, np.ndarray):
            vector = vector.tolist()
        if not isinstance(vector, (list, tuple)) or len(vector) != 3:
            raise ArgumentError("normals", value=normals, caller=caller, message=None)
        components = []
        for component in vector:
            if isinstance(component, bool) or not isinstance(component, (int, float, np.number)):
                raise ArgumentError("normals", value=normals, caller=caller, message=None)
            fc = float(component)
            if not np.isfinite(fc):
                raise ArgumentError("normals", value=normals, caller=caller, message=None)
            components.append(fc)
        out.append(components)
    return out
