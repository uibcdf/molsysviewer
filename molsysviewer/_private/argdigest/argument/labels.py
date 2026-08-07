from ...exceptions import ArgumentError
from ..helpers import normalize_viewer_caller


def digest_labels(labels, caller=None):
    caller = normalize_viewer_caller(caller)
    if labels is None:
        return None
    if caller == "molsysviewer.viewer.clear_decorations" and isinstance(labels, bool):
        return labels
    if isinstance(labels, str):
        return [labels]
    if isinstance(labels, (list, tuple)) and all(isinstance(item, str) for item in labels):
        return list(labels)
    raise ArgumentError("labels", value=labels, caller=caller, message=None)
