from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_message(message, caller=None):
    if isinstance(message, Mapping):
        return message
    raise ArgumentError("message", value=message, caller=caller)
