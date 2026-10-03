from ...exceptions import ArgumentError


def digest_assume_complete_connectivity(assume_complete_connectivity, caller=None):
    if isinstance(assume_complete_connectivity, bool):
        return assume_complete_connectivity
    raise ArgumentError("assume_complete_connectivity", value=assume_complete_connectivity, caller=caller)
