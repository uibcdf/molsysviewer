from .._interaction_arguments import digest_positive_integer


def digest_max_cyclic_block_size(max_cyclic_block_size, caller=None):
    return digest_positive_integer(max_cyclic_block_size, "max_cyclic_block_size", caller)
