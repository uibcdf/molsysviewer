from ...exceptions import ArgumentError


def digest_session_id(session_id, caller=None):
    if isinstance(session_id, str) and session_id.strip():
        return session_id
    raise ArgumentError("session_id", value=session_id, caller=caller)
