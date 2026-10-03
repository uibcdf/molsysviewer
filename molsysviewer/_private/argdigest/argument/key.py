from ...exceptions import ArgumentError


def digest_key(key, caller=None):
    """Widget-state lookup accepts no key, one name or a list of names."""
    if key is None or isinstance(key, str):
        return key
    if isinstance(key, (list, tuple)) and all(isinstance(item, str) for item in key):
        return key
    raise ArgumentError("key", value=key, caller=caller)
