from collections.abc import Sequence
from pathlib import Path

from molsysviewer._private.exceptions import ArgumentError
from ..helpers import normalize_viewer_caller

_EXPORT_CALLERS = {
    "molsysviewer.exports.html",
    "molsysviewer.exports.ExportManager.html",
    "molsysviewer.viewer.write_html",
    "molsysviewer.viewer.MolSysView.write_html",
}


def digest_shared_runtime(shared_runtime, caller=None):

    caller = normalize_viewer_caller(caller)

    # Absent means "self-contained"; the callee applies that default.
    if shared_runtime is None:
        return None

    if caller in _EXPORT_CALLERS:
        if isinstance(shared_runtime, Path):
            return str(shared_runtime)
        if isinstance(shared_runtime, str) and shared_runtime:
            # "cdn" is the one reserved value. A directory of that name is
            # addressable as "./cdn" or by absolute path.
            return shared_runtime
        if isinstance(shared_runtime, Sequence) and not isinstance(shared_runtime, (bytes, bytearray)):
            candidates = list(shared_runtime)
            if candidates and all(isinstance(item, str) and item for item in candidates):
                return candidates

    raise ArgumentError('shared_runtime', value=shared_runtime, caller=caller, message=None)
