from molsysviewer._private.exceptions import ArgumentError

functions_with_boolean = (
        'molsysmt.basic.get.get',
        'molsysmt.basic.compare.compare',
        'molsysviewer.viewer.get',
        )


def digest_n_atoms(n_atoms, caller=None):

    if caller.endswith(functions_with_boolean):
        if isinstance(n_atoms, bool):
            return n_atoms
        else:
            raise ArgumentError('n_atoms', value=n_atoms, caller=caller, message=None)
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_atoms, (bool, int)):
            return n_atoms
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_atoms, (bool, int)):
            return n_atoms
    elif caller=='molsysmt.native.topology.__init__':
        if isinstance(n_atoms, int):
            return n_atoms
    elif caller=='molsysmt.native.molsys.__init__':
        if isinstance(n_atoms, int):
            return n_atoms

    raise ArgumentError('n_atoms', value=n_atoms, caller=caller, message=None)
