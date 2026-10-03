from ...exceptions import ArgumentError


def digest_source_endpoint_id(source_endpoint_id, caller=None):
    if isinstance(source_endpoint_id, str) and source_endpoint_id.strip():
        return source_endpoint_id
    raise ArgumentError("source_endpoint_id", value=source_endpoint_id, caller=caller)
