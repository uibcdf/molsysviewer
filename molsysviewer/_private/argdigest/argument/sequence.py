from ...exceptions import ArgumentError


def digest_sequence(sequence, caller=None):

    if isinstance(sequence, str):
        return sequence

    raise ArgumentError("sequence", value=sequence, caller=caller, message=None)
