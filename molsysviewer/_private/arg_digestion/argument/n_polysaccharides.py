from molsysviewer._private.exceptions import ArgumentError

def digest_n_polysaccharides(n_polysaccharides, caller=None):

    if caller=='molsysmt.basic.get.get':
        if isinstance(n_polysaccharides, bool):
            return n_polysaccharides
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_polysaccharides, (bool, int)):
            return n_polysaccharides
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_polysaccharides, (bool, int)):
            return n_polysaccharides

    raise ArgumentError('n_polysaccharides', value=n_polysaccharides, caller=caller, message=None)

