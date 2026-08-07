from ...exceptions import ArgumentError


def digest_description(description, caller=None):
    if description is None or isinstance(description, str):
        return description
    raise ArgumentError("description", value=description, caller=caller, message=None)
