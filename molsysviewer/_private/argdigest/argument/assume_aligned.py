from ...exceptions import ArgumentError


def digest_assume_aligned(assume_aligned, caller=None):
    if isinstance(assume_aligned, bool):
        return assume_aligned
    raise ArgumentError("assume_aligned", value=assume_aligned, caller=caller)
