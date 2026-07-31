from molsysviewer._private.exceptions import ArgumentError

def digest_n_bioassemblies(n_bioassemblies, caller=None):

    if caller in ('molsysmt.basic.get.get', 'molsysviewer.viewer.get'):
        if isinstance(n_bioassemblies, bool):
            return n_bioassemblies

    raise ArgumentError('n_bioassemblies', value=n_bioassemblies, caller=caller, message=None)

