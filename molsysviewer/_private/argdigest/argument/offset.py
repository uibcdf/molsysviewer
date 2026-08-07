from ...exceptions import ArgumentError


def digest_offset(offset, caller=None):
    if isinstance(offset, (list, tuple)) and len(offset) == 3:
        try:
            return [float(x) for x in offset]
        except (TypeError, ValueError):
            pass
    raise ArgumentError("offset", value=offset, caller=caller, message=None)
