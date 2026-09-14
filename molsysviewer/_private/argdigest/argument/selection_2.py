from molsysviewer._private.exceptions import ArgumentError


def digest_selection_2(selection_2, syntax="MolSysMT", caller=None):

    if selection_2 is None:
        return None

    from .selection import digest_selection

    try:
        return digest_selection(selection_2, syntax=syntax, caller=caller)
    except:  # noqa: E722
        raise ArgumentError("selection_2", value=selection_2, caller=caller, message=None)
