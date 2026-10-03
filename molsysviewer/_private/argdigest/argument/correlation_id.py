from ...exceptions import ArgumentError


def digest_correlation_id(correlation_id, caller=None):
    if correlation_id is None:
        return None
    if isinstance(correlation_id, str) and correlation_id.strip():
        return correlation_id
    raise ArgumentError("correlation_id", value=correlation_id, caller=caller)
