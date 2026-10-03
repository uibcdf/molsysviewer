from ...exceptions import ArgumentError


def digest_capabilities(capabilities, caller=None):
    if isinstance(capabilities, (str, bytes)):
        raise ArgumentError("capabilities", value=capabilities, caller=caller)
    try:
        values = tuple(capabilities)
    except TypeError:
        raise ArgumentError("capabilities", value=capabilities, caller=caller) from None
    if all(isinstance(value, str) and value.strip() for value in values):
        return values
    raise ArgumentError("capabilities", value=capabilities, caller=caller)
