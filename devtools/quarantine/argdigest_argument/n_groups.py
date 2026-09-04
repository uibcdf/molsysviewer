from molsysviewer._private.exceptions import ArgumentError

functions_with_boolean = (
        'molsysmt.basic.get.get',
        'molsysmt.basic.compare.compare',
        'molsysviewer.viewer.get',
        )


def digest_n_groups(n_groups, caller=None):

    if caller.endswith(functions_with_boolean):
        if isinstance(n_groups, bool):
            return n_groups
        else:
            raise ArgumentError('n_groups', value=n_groups, caller=caller, message=None)
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_groups, (bool, int)):
            return n_groups
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_groups, (bool, int)):
            return n_groups
    elif caller=='molsysmt.native.topology.__init__':
        if isinstance(n_groups, int):
            return n_groups
    elif caller=='molsysmt.native.molsys.__init__':
        if isinstance(n_groups, int):
            return n_groups

    raise ArgumentError('n_groups', value=n_groups, caller=caller, message=None)

