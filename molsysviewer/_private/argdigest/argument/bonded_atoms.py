from molsysviewer._private.exceptions import ArgumentError

def digest_bonded_atoms(bonded_atoms, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(bonded_atoms, bool):
            return bonded_atoms

    raise ArgumentError('bonded_atoms', value=bonded_atoms, caller=caller, message=None)

