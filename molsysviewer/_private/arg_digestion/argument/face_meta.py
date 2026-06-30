import json

from ...exceptions import ArgumentError


def digest_face_meta(face_meta, caller=None):
    if face_meta is None:
        return None
    try:
        entries = [dict(entry) for entry in face_meta]
    except (TypeError, ValueError) as exc:
        raise ArgumentError("face_meta", value=face_meta, caller=caller, message=None) from exc
    try:
        json.dumps(entries)
    except TypeError as exc:
        raise ArgumentError("face_meta", value=face_meta, caller=caller, message="face_meta must be JSON-serializable") from exc
    return entries
