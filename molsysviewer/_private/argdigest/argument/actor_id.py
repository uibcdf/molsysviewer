from ...exceptions import ArgumentError


def digest_actor_id(actor_id, caller=None):
    if actor_id is None:
        return None
    if isinstance(actor_id, str) and actor_id.strip():
        return actor_id
    raise ArgumentError("actor_id", value=actor_id, caller=caller)
