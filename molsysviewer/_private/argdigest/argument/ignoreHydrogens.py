from ...representation_params import digest_curated_parameter


def digest_ignoreHydrogens(ignoreHydrogens, caller=None):
    return digest_curated_parameter("ignoreHydrogens", ignoreHydrogens, caller=caller)
