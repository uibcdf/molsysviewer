from ...representation_params import digest_curated_parameter


def digest_helixProfile(helixProfile, caller=None):
    return digest_curated_parameter("helixProfile", helixProfile, caller=caller)
