from molsysviewer._private.exceptions import ArgumentError


def digest_budget_bytes(budget_bytes, caller=None):
    """A byte ceiling: a non-negative integer, where 0 silences the warning.

    Booleans are rejected even though `bool` is an `int`: `True` would silently
    become a one-byte budget, so every load would warn.
    """
    if isinstance(budget_bytes, bool):
        raise ArgumentError('budget_bytes', value=budget_bytes, caller=caller, message=None)
    if isinstance(budget_bytes, int) and budget_bytes >= 0:
        return budget_bytes

    raise ArgumentError('budget_bytes', value=budget_bytes, caller=caller, message=None)
