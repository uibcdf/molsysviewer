from ...exceptions import ArgumentError


def digest_snapshot(snapshot, caller=None):
    if isinstance(snapshot, dict):
        return dict(snapshot)
    raise ArgumentError("snapshot", value=snapshot, caller=caller, message=None)
