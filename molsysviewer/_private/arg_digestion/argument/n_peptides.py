from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

def digest_n_peptides(n_peptides, caller=None):
    caller = normalize_viewer_caller(caller)

    if caller=='molsysmt.basic.get.get':
        if isinstance(n_peptides, bool):
            return n_peptides
    elif caller in ('molsysmt.basic.contains.contains', 'molsysviewer.viewer.contains', 'molsysviewer.whole.contains', 'molsysviewer.regions.contains'):
        if isinstance(n_peptides, (bool, int)):
            return n_peptides
    elif caller in ('molsysmt.basic.is_composed_of.is_composed_of', 'molsysviewer.viewer.is_composed_of', 'molsysviewer.whole.is_composed_of', 'molsysviewer.regions.is_composed_of'):
        if isinstance(n_peptides, (bool, int)):
            return n_peptides

    raise ArgumentError('n_peptides', value=n_peptides, caller=caller, message=None)
