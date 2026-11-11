from ...exceptions import ArgumentError


def digest_resolution(resolution, caller=None):
    if caller in {
        "molsysviewer.whole.set_representation",
        "molsysviewer.regions.set_representation",
        "molsysviewer.regions.add",
        "molsysviewer.styles.apply",
        "molsysviewer.styles.focus",
    }:
        from ...representation_params import digest_curated_parameter

        return digest_curated_parameter("resolution", resolution, caller=caller)
    if resolution is None:
        return None
    if isinstance(resolution, (int, float)) and not isinstance(resolution, bool):
        return float(resolution)
    raise ArgumentError("resolution", value=resolution, caller=caller, message=None)
