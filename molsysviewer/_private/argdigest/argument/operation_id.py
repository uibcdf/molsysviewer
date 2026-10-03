from ...exceptions import ArgumentError


def digest_operation_id(operation_id, caller=None):
    if operation_id is None:
        return None
    if isinstance(operation_id, str) and operation_id.strip():
        return operation_id
    raise ArgumentError("operation_id", value=operation_id, caller=caller)
