from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._private.variables import is_iterable
import numpy as np

#: `selection` means a MolSysMT selection expression everywhere in this library except in
#: the add-on context-menu path, where it is the frontend's selection *payload* -- a dict
#: such as `{"kind": "structure", "atom_indices": [...]}` describing what the user has
#: picked in the canvas. It is data arriving from the browser, not an expression to
#: resolve, so it is passed through and the builders read the keys they know.
_FRONTEND_SELECTION_PAYLOAD_CALLERS = frozenset({
    "molsysviewer.addons.build_context_items",
    "molsysviewer.addons.refresh_context_items",
})


def digest_selection(selection, syntax="MolSysMT", caller=None):
    """ Checks if a given selection has the correct type and syntax

        Parameters
        ----------
        item : str or list of int
            An instance of one of the forms supported by MolSysMT.
        syntax : str, default="MolSysMT"
            Name of the syntax used in the selection.
        caller: str, optional
            Name of the function or method that is being digested.

        Raises
        ------
        WrongSelectionError or WrongSelectionSyntaxError or WrongSyntaxError
            A WrongSelectionError is raised if the selection object is not in deed a selection.
            A WrongSelectionSyntaxError is raised if the selection is not using the expected
            syntax.
            A WrongSyntaxError is raised if the syntax given is not in deed a syntax.

    """

    if caller in _FRONTEND_SELECTION_PAYLOAD_CALLERS:
        return selection

    if syntax=='MolSysMT':
        if isinstance(selection, str):
            return selection
        elif isinstance(selection, (int, np.int64, np.int32)):
            return [selection]
        elif is_iterable(selection):
            if all([isinstance(ii, (int, np.int64, np.int32)) for ii in selection]):
                return list(selection)
            else:
                return list([digest_selection(ii, syntax=syntax, caller=caller) for ii in selection])
        elif isinstance(selection, range):
            return list(selection)
        elif selection is None:
            return None
    else:
        if isinstance(selection, str):
            return selection
        elif isinstance(selection, (int, np.int64, np.int32)):
            return np.array([selection], dtype='int64')
        elif isinstance(selection, (np.ndarray, list, tuple, range)):
            return np.array(selection, dtype='int64')
        elif isinstance(selection, range):
            return list(selection)
        elif selection is None:
            return None

    raise ArgumentError('selection', value=selection, caller=caller, message=None)

