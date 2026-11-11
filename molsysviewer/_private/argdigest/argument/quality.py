from ...representation_params import digest_curated_parameter


def digest_quality(quality, caller=None):
    return digest_curated_parameter("quality", quality, caller=caller)
