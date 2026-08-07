import json

from ...exceptions import ArgumentError


def digest_edge_meta(edge_meta, caller=None):
    if edge_meta is None:
        return None
    try:
        entries = [dict(entry) for entry in edge_meta]
    except (TypeError, ValueError) as exc:
        raise ArgumentError("edge_meta", value=edge_meta, caller=caller, message=None) from exc
    try:
        json.dumps(entries)
    except TypeError as exc:
        raise ArgumentError("edge_meta", value=edge_meta, caller=caller, message="edge_meta must be JSON-serializable") from exc
    return entries
