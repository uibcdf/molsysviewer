from molsysviewer._private.exceptions import ArgumentError

def digest_n_amino_acids(n_amino_acids, caller=None):

    if caller=='molsysmt.basic.get.get':
        if isinstance(n_amino_acids, bool):
            return n_amino_acids
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_amino_acids, (bool, int)):
            return n_amino_acids


    raise ArgumentError('n_amino_acids', value=n_amino_acids, caller=caller, message=None)

