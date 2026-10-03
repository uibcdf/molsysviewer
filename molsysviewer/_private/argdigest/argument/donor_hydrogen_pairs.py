from .._interaction_arguments import digest_index_array


def digest_donor_hydrogen_pairs(donor_hydrogen_pairs, caller=None):
    return digest_index_array(donor_hydrogen_pairs, "donor_hydrogen_pairs", caller, pairs=True)
