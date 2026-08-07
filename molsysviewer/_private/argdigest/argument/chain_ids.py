from ...exceptions import ArgumentError


def digest_chain_ids(chain_ids, caller=None):
    if chain_ids is None:
        return None
    if isinstance(chain_ids, (list, tuple)) and all(isinstance(item, str) for item in chain_ids):
        return list(chain_ids)
    raise ArgumentError("chain_ids", value=chain_ids, caller=caller, message=None)
