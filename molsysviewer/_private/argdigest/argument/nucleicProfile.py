from ...representation_params import digest_curated_parameter


def digest_nucleicProfile(nucleicProfile, caller=None):
    return digest_curated_parameter("nucleicProfile", nucleicProfile, caller=caller)
