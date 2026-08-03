from collections.abc import Sequence

from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

_EXPORT_CALLERS = {
    "molsysviewer.exports.html",
    "molsysviewer.exports.ExportManager.html",
    "molsysviewer.viewer.write_html",
    "molsysviewer.viewer.MolSysView.write_html",
}


def digest_runtime(runtime, caller=None):

    caller = normalize_viewer_caller(caller)

    # `runtime` is optional: the callee applies the mode-dependent default.
    if runtime is None:
        return None

    if caller in _EXPORT_CALLERS:
        if isinstance(runtime, str):
            if runtime in ["local", "cdn"]:
                return runtime
        elif isinstance(runtime, Sequence) and not isinstance(runtime, (bytes, bytearray)):
            candidates = list(runtime)
            if candidates and all(isinstance(item, str) and item for item in candidates):
                return candidates

    raise ArgumentError('runtime', value=runtime, caller=caller, message=None)
