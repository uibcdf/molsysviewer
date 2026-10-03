from ...exceptions import ArgumentError


def digest_target_endpoint_id(target_endpoint_id, caller=None):
    if target_endpoint_id is None:
        return None
    if isinstance(target_endpoint_id, str) and target_endpoint_id.strip():
        return target_endpoint_id
    raise ArgumentError("target_endpoint_id", value=target_endpoint_id, caller=caller)
