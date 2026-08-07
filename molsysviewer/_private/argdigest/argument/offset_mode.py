from ...exceptions import ArgumentError


def digest_offset_mode(offset_mode, caller=None):
    if isinstance(offset_mode, str) and offset_mode in {"camera", "world"}:
        return offset_mode
    raise ArgumentError("offset_mode", value=offset_mode, caller=caller, message=None)
