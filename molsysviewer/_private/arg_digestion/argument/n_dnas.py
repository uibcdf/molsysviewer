from molsysviewer._private.exceptions import ArgumentError

def digest_n_dnas(n_dnas, caller=None):

    if caller=='molsysmt.basic.get.get':
        if isinstance(n_dnas, bool):
            return n_dnas
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_dnas, (bool, int)):
            return n_dnas
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_dnas, (bool, int)):
            return n_dnas

    raise ArgumentError('n_dnas', value=n_dnas, caller=caller, message=None)

