from molsysviewer._private.exceptions import ArgumentError

def digest_n_proteins(n_proteins, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(n_proteins, bool):
            return n_proteins
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_proteins, (bool, int)):
            return n_proteins
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_proteins, (bool, int)):
            return n_proteins

    raise ArgumentError('n_proteins', value=n_proteins, caller=caller, message=None)

