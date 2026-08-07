from ...exceptions import ArgumentError


def digest_pocket_ids(pocket_ids, caller=None):
    if pocket_ids is None:
        return None
    if isinstance(pocket_ids, (list, tuple)) and all(isinstance(item, (int, str)) for item in pocket_ids):
        return list(pocket_ids)
    raise ArgumentError("pocket_ids", value=pocket_ids, caller=caller, message=None)
