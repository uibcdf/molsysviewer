from ...exceptions import ArgumentError


def digest_interactions_policy(interactions_policy, caller=None):
    if isinstance(interactions_policy, str) and interactions_policy in {"invalidate", "preserve"}:
        return interactions_policy
    raise ArgumentError("interactions_policy", value=interactions_policy, caller=caller)
