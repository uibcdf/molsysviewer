from molsysviewer._private.exceptions import ArgumentError


def digest_include_overlays(include_overlays, caller=None):
    if type(include_overlays) is not bool:
        raise ArgumentError("include_overlays", value=include_overlays, caller=caller)
    return include_overlays
