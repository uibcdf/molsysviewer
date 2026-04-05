from molsysviewer._private.exceptions import ArgumentError

def digest_n_ions(n_ions, caller=None):

    if caller=='molsysmt.basic.get.get':
        if isinstance(n_ions, bool):
            return n_ions
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_ions, (bool, int)):
            return n_ions
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_ions, (bool, int)):
            return n_ions

    raise ArgumentError('n_ions', value=n_ions, caller=caller, message=None)

