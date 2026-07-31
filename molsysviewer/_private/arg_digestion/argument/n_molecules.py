from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

functions_with_boolean = (
        'molsysmt.basic.get.get',
        'molsysmt.basic.compare.compare',
        'molsysviewer.viewer.get',
        )


def digest_n_molecules(n_molecules, caller=None):
    caller = normalize_viewer_caller(caller)

    if caller.endswith(functions_with_boolean):
        if isinstance(n_molecules, bool):
            return n_molecules
        else:
            raise ArgumentError('n_molecules', value=n_molecules, caller=caller, message=None)
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_molecules, (bool, int)):
            return n_molecules
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_molecules, (bool, int)):
            return n_molecules
    elif caller=='molsysmt.native.topology.__init__':
        if isinstance(n_molecules, int):
            return n_molecules
    elif caller=='molsysmt.native.molsys.__init__':
        if isinstance(n_molecules, int):
            return n_molecules

    raise ArgumentError('n_molecules', value=n_molecules, caller=caller, message=None)
