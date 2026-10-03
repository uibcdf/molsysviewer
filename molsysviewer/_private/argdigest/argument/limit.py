from ...exceptions import ArgumentError


def digest_limit(limit, caller=None):
    if isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= 200:
        return limit
    raise ArgumentError("limit", value=limit, caller=caller)
