from ...exceptions import ArgumentError


def digest_request(request, caller=None):
    from ....runtime_contract import RuntimeEnvelope

    if isinstance(request, RuntimeEnvelope):
        return request
    raise ArgumentError("request", value=request, caller=caller)
