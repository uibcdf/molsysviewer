"""`expected_session_id` is the session a remote packet must claim to be accepted.

One of a family of three — with `expected_viewer_id` and `expected_endpoint_id` — that
share a rule; it lives in `_shared.check_expected_identity`.
"""

from .._shared import check_expected_identity


def digest_expected_session_id(expected_session_id, caller=None):
    return check_expected_identity("expected_session_id", expected_session_id, caller=caller)
