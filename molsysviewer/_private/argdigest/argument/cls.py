from ...exceptions import ArgumentError


def digest_cls(cls, caller=None):
    """Validate the owner bound by a public class method."""
    if isinstance(cls, type):
        return cls
    raise ArgumentError("cls", value=cls, caller=caller)
