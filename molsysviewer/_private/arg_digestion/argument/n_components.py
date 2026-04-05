from molsysviewer._private.exceptions import ArgumentError

functions_with_boolean = (
        'molsysmt.basic.get.get',
        'molsysmt.basic.compare.compare',
        )


def digest_n_components(n_components, caller=None):

    if caller.endswith(functions_with_boolean):
        if isinstance(n_components, bool):
            return n_components
        else:
            raise ArgumentError('n_components', value=n_components, caller=caller, message=None)
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_components, (bool, int)):
            return n_components
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_components, (bool, int)):
            return n_components
    elif caller=='molsysmt.native.topology.__init__':
        if isinstance(n_components, int):
            return n_components
    elif caller=='molsysmt.native.molsys.__init__':
        if isinstance(n_components, int):
            return n_components

    raise ArgumentError('n_components', value=n_components, caller=caller, message=None)

