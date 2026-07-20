from ...exceptions import ArgumentError


def digest_target(target, caller=None):
    """Digest the name of a target a setting applies to.

    Accepts a non-empty string, returned stripped and lowercased to match the
    keys callers look up. Which names are valid depends on the caller's own
    registry, so that check stays with the callee, which raises listing the
    allowed values.
    """
    if isinstance(target, str):
        normalized = target.strip().lower()
        if normalized:
            return normalized

    raise ArgumentError("target", value=target, caller=caller, message=None)
