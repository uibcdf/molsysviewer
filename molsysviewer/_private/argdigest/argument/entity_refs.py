import json

from ...exceptions import ArgumentError


def digest_entity_refs(entity_refs, caller=None):
    if entity_refs is None:
        return None
    try:
        refs = list(entity_refs)
    except TypeError as exc:
        raise ArgumentError("entity_refs", value=entity_refs, caller=caller, message=None) from exc
    try:
        json.dumps(refs)
    except TypeError as exc:
        raise ArgumentError("entity_refs", value=entity_refs, caller=caller, message="entity_refs must be JSON-serializable") from exc
    return refs
