from .._interaction_arguments import digest_positive_integer


def digest_max_matches(max_matches, caller=None):
    return digest_positive_integer(max_matches, "max_matches", caller)
