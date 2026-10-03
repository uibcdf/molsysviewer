from ...exceptions import ArgumentError


def digest_owner(owner, caller=None):
    if isinstance(owner, str) and owner.strip():
        return owner.strip()
    raise ArgumentError("owner", value=owner, caller=caller)
