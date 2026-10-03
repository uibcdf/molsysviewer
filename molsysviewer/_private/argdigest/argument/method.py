from ...exceptions import ArgumentError


def digest_method(method, caller=None):

    if caller and caller.startswith("molsysviewer.interactions."):
        if isinstance(method, str):
            return method.strip().lower()
        raise ArgumentError("method", value=method, caller=caller)

    if caller == "molsysmt.structure.align.align":
        if isinstance(method, str):
            return method

    return ArgumentError("method", value=method, caller=caller, message=None)
