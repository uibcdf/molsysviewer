from molsysviewer._private.exceptions import ArgumentError


def digest_load_mode(load_mode, caller=None):
    if isinstance(load_mode, str):
        if load_mode in ("selection", "all"):
            return load_mode
    raise ArgumentError("load_mode", value=load_mode, caller=caller, message=None)
