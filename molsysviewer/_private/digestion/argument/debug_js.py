from molsysviewer._private.exceptions import ArgumentError


def digest_debug_js(debug_js, caller=None):
    if debug_js is None:
        return None
    if isinstance(debug_js, bool):
        return debug_js
    raise ArgumentError("debug_js", value=debug_js, caller=caller, message=None)
