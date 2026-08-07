from molsysviewer._private.exceptions import ArgumentError


def digest_selection_d(selection_d, syntax="MolSysMT", caller=None):
    if selection_d is None:
        return None
    from .selection import digest_selection
    try:
        return digest_selection(selection_d, syntax=syntax, caller=caller)
    except Exception:
        raise ArgumentError('selection_d', value=selection_d, caller=caller, message=None)
