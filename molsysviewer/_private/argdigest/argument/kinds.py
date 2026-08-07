from ...exceptions import ArgumentError


def digest_kinds(kinds, caller=None):
    """Digest the interaction-site kinds, one label per site.

    The labels are free-form (they key the colour table/scheme), so only their
    shape is validated: a non-empty sequence of non-empty strings, stripped.
    """
    if not isinstance(kinds, (list, tuple)):
        raise ArgumentError("kinds", value=kinds, caller=caller, message=None)

    out = []
    for kind in kinds:
        if not isinstance(kind, str):
            raise ArgumentError("kinds", value=kinds, caller=caller, message=None)
        normalized = kind.strip()
        if not normalized:
            raise ArgumentError("kinds", value=kinds, caller=caller, message=None)
        out.append(normalized)

    if not out:
        raise ArgumentError("kinds", value=kinds, caller=caller, message=None)
    return out
