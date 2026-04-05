from molsysviewer._private.exceptions import ArgumentError

functions_with_boolean = (
        'molsysmt.basic.get.get',
        'molsysmt.basic.compare.compare',
        )


def digest_n_entities(n_entities, caller=None):

    if caller.endswith(functions_with_boolean):
        if isinstance(n_entities, bool):
            return n_entities
        else:
            raise ArgumentError('n_entities', value=n_entities, caller=caller, message=None)
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_entities, (bool, int)):
            return n_entities
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_entities, (bool, int)):
            return n_entities
    elif caller=='molsysmt.native.topology.__init__':
        if isinstance(n_entities, int):
            return n_entities
    elif caller=='molsysmt.native.molsys.__init__':
        if isinstance(n_entities, int):
            return n_entities

    raise ArgumentError('n_entities', value=n_entities, caller=caller, message=None)

