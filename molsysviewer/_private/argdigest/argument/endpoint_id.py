from ...exceptions import ArgumentError


def digest_endpoint_id(endpoint_id, caller=None):
    if isinstance(endpoint_id, str) and endpoint_id.strip():
        return endpoint_id
    raise ArgumentError("endpoint_id", value=endpoint_id, caller=caller)
