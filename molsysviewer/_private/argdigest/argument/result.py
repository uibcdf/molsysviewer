from ...exceptions import ArgumentError


def digest_result(result, caller=None):
    import molsysmt as msm

    if isinstance(result, getattr(msm, "Interactions", ())):
        return result
    raise ArgumentError("result", value=type(result).__name__, caller=caller)
