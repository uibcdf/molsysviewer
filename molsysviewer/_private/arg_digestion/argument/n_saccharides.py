from molsysviewer._private.exceptions import ArgumentError

def digest_n_saccharides(n_saccharides, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(n_saccharides, bool):
            return n_saccharides
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_saccharides, (bool, int)):
            return n_saccharides
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_saccharides, (bool, int)):
            return n_saccharides

    raise ArgumentError('n_saccharides', value=n_saccharides, caller=caller, message=None)

