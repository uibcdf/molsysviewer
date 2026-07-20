from ...exceptions import ArgumentError


def digest_transaction_id(transaction_id, caller=None):
    """Digest the optional identifier correlating a request with its ack.

    Accepts ``None`` (no acknowledgement wanted), an ``int``, or a non-empty
    string. The value is echoed back by the frontend, so it is passed through
    unchanged rather than coerced to a single type.
    """
    if transaction_id is None:
        return None

    if isinstance(transaction_id, bool):
        raise ArgumentError("transaction_id", value=transaction_id, caller=caller, message=None)

    if isinstance(transaction_id, int):
        return transaction_id

    if isinstance(transaction_id, str):
        normalized = transaction_id.strip()
        if normalized:
            return normalized

    raise ArgumentError("transaction_id", value=transaction_id, caller=caller, message=None)
