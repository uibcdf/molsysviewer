from molsysviewer._private.exceptions import ArgumentError

def digest_bond_order(bond_order, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(bond_order, bool):
            return bond_order

    raise ArgumentError('bond_order', value=bond_order, caller=caller, message=None)

