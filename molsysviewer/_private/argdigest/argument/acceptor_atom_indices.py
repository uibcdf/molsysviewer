from .._interaction_arguments import digest_index_array


def digest_acceptor_atom_indices(acceptor_atom_indices, caller=None):
    return digest_index_array(acceptor_atom_indices, "acceptor_atom_indices", caller, pairs=False)
