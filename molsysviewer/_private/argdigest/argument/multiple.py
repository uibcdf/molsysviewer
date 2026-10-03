from ...exceptions import ArgumentError


def digest_multiple(multiple, caller=None):
    if isinstance(multiple, bool):
        return multiple
    raise ArgumentError("multiple", value=multiple, caller=caller, message="expected a boolean")
