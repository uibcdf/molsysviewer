from molsysviewer._private.exceptions import ArgumentError


def digest_selection_b(selection_b, syntax="MolSysMT", caller=None):
    if selection_b is None:
        return None
    from .selection import digest_selection
    try:
        return digest_selection(selection_b, syntax=syntax, caller=caller)
    except Exception:
        raise ArgumentError('selection_b', value=selection_b, caller=caller, message=None)
