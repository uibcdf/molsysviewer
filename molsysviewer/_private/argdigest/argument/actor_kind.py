from ...exceptions import ArgumentError


def digest_actor_kind(actor_kind, caller=None):
    if actor_kind is None:
        return None
    if isinstance(actor_kind, str) and actor_kind.strip():
        return actor_kind
    raise ArgumentError("actor_kind", value=actor_kind, caller=caller)
