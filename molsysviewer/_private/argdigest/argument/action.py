from ...exceptions import ArgumentError


def digest_action(action, caller=None):
    if isinstance(action, str) and action.strip():
        return action
    raise ArgumentError("action", value=action, caller=caller)
