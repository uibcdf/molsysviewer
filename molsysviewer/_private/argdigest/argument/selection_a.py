from molsysviewer._private.exceptions import ArgumentError


def digest_selection_a(selection_a, syntax="MolSysMT", caller=None):
    if selection_a is None:
        return None
    from .selection import digest_selection
    try:
        return digest_selection(selection_a, syntax=syntax, caller=caller)
    except Exception:
        raise ArgumentError('selection_a', value=selection_a, caller=caller, message=None)
