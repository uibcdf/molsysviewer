from ...representation_params import digest_curated_parameter


def digest_multipleBonds(multipleBonds, caller=None):
    return digest_curated_parameter("multipleBonds", multipleBonds, caller=caller)
