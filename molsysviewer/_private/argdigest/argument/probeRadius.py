from ...representation_params import digest_curated_parameter


def digest_probeRadius(probeRadius, caller=None):
    return digest_curated_parameter("probeRadius", probeRadius, caller=caller)
