from ...exceptions import ArgumentError


def digest_stem(stem, caller=None):
    if isinstance(stem, str) and stem.strip():
        return stem.strip()
    raise ArgumentError("stem", value=stem, caller=caller, message=None)
