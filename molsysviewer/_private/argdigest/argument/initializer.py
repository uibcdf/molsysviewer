from ...exceptions import ArgumentError


def digest_initializer(initializer, caller=None):
    if not callable(initializer):
        raise ArgumentError(
            "initializer", value=initializer, caller=caller, message="Expected a callable View initializer."
        )
    return initializer
