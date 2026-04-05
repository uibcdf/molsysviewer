from molsysviewer._private.exceptions import ArgumentError

def digest_n_rnas(n_rnas, caller=None):

    if caller=='molsysmt.basic.get.get':
        if isinstance(n_rnas, bool):
            return n_rnas
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_rnas, (bool, int)):
            return n_rnas
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_rnas, (bool, int)):
            return n_rnas

    raise ArgumentError('n_rnas', value=n_rnas, caller=caller, message=None)

