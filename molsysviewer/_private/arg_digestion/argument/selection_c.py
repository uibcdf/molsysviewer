from molsysviewer._private.exceptions import ArgumentError


def digest_selection_c(selection_c, syntax="MolSysMT", caller=None):
    if selection_c is None:
        return None
    from .selection import digest_selection
    try:
        return digest_selection(selection_c, syntax=syntax, caller=caller)
    except Exception:
        raise ArgumentError('selection_c', value=selection_c, caller=caller, message=None)
