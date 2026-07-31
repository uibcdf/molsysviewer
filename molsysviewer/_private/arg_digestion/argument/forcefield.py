from molsysviewer._private.exceptions import ArgumentError

def digest_forcefield(forcefield, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(forcefield, bool):
            return forcefield

    if isinstance(forcefield, str):
        from molsysmt.attribute import attributes
        if forcefield in attributes['forcefield']['values']:
            return forcefield

    raise ArgumentError('forcefield', value=forcefield, caller=caller, message=None)

