from ...exceptions import ArgumentError


def digest_preset(preset, caller=None):
    if preset is None or isinstance(preset, str):
        return preset
    raise ArgumentError("preset", value=preset, caller=caller, message=None)
