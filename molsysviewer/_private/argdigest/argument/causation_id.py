from ...exceptions import ArgumentError


def digest_causation_id(causation_id, caller=None):
    if causation_id is None:
        return None
    if isinstance(causation_id, str) and causation_id.strip():
        return causation_id
    raise ArgumentError("causation_id", value=causation_id, caller=caller)
