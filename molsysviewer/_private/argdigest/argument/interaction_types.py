from ...exceptions import ArgumentError


def digest_interaction_types(interaction_types, caller=None):
    if interaction_types is None:
        return None
    if isinstance(interaction_types, str):
        interaction_types = [interaction_types]
    if isinstance(interaction_types, (list, tuple, set)) and all(
        isinstance(kind, str) and kind for kind in interaction_types
    ):
        return list(interaction_types)
    raise ArgumentError("interaction_types", value=interaction_types, caller=caller)
