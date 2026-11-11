from ...representation_params import digest_curated_parameter


def digest_sizeFactor(sizeFactor, caller=None):
    return digest_curated_parameter("sizeFactor", sizeFactor, caller=caller)
