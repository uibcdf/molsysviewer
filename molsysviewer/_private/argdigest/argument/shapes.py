from ...exceptions import ArgumentError


def digest_shapes(shapes, caller=None):
    if isinstance(shapes, bool):
        return shapes
    raise ArgumentError("shapes", value=shapes, caller=caller, message=None)
