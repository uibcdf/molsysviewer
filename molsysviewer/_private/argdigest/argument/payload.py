from ...exceptions import ArgumentError


def digest_payload(payload, caller=None):
    if isinstance(payload, dict):
        return dict(payload)
    raise ArgumentError("payload", value=payload, caller=caller, message=None)
