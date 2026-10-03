from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_updates(updates, caller=None):
    if isinstance(updates, Mapping):
        return dict(updates)
    raise ArgumentError("updates", value=updates, caller=caller)
