from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_payload(payload, caller=None):
    if isinstance(payload, Mapping):
        return dict(payload)
    raise ArgumentError("payload", value=payload, caller=caller, message=None)
