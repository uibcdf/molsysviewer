from ...exceptions import ArgumentError


def digest_deadline_unix_ms(deadline_unix_ms, caller=None):
    if (
        deadline_unix_ms is None
        or isinstance(deadline_unix_ms, int)
        and not isinstance(deadline_unix_ms, bool)
        and deadline_unix_ms >= 0
    ):
        return deadline_unix_ms
    raise ArgumentError("deadline_unix_ms", value=deadline_unix_ms, caller=caller)
