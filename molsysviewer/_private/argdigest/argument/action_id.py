from ...exceptions import ArgumentError


def digest_action_id(action_id, caller=None):
    if isinstance(action_id, str) and action_id.strip():
        return action_id.strip()
    raise ArgumentError("action_id", value=action_id, caller=caller, message=None)
