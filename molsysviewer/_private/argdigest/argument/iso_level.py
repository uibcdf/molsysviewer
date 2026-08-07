from ...exceptions import ArgumentError


def digest_iso_level(iso_level, caller=None):
    if iso_level is None:
        return None
    if isinstance(iso_level, (int, float)) and not isinstance(iso_level, bool):
        return float(iso_level)
    raise ArgumentError("iso_level", value=iso_level, caller=caller, message=None)
