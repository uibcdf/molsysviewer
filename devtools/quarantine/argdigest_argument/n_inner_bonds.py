from molsysviewer._private.exceptions import ArgumentError

def digest_n_inner_bonds(n_inner_bonds, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(n_inner_bonds, bool):
            return n_inner_bonds
        elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
            if isinstance(n_inner_bonds, (bool, int)):
                return n_inner_bonds

    raise ArgumentError('n_inner_bonds', values=n_inner_bonds, caller=caller, message=None)

