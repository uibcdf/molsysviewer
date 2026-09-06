"""`expected_viewer_id` is the viewer a remote packet must claim to be accepted.

One of a family of three — with `expected_session_id` and `expected_endpoint_id` — that
share a rule; it lives in `_shared.check_expected_identity`, which says why the value is
compared unstripped and why blank is refused.
"""

from .._shared import check_expected_identity


def digest_expected_viewer_id(expected_viewer_id, caller=None):
    return check_expected_identity("expected_viewer_id", expected_viewer_id, caller=caller)
