from ...exceptions import ArgumentError


def digest_palette(palette, caller=None):
    if palette is None:
        return None
    if isinstance(palette, str):
        return palette
    if isinstance(palette, (list, tuple)):
        return list(palette)
    if hasattr(palette, "name") or hasattr(palette, "__call__"):
        return palette
    raise ArgumentError("palette", value=palette, caller=caller, message=None)
