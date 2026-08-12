"""`start_time_ms` is a point on the movie timeline, in milliseconds.

One of a family of four that share a rule; it lives in `_shared.check_milliseconds`.
"""

from .._shared import check_milliseconds


def digest_start_time_ms(start_time_ms, caller=None):
    return check_milliseconds("start_time_ms", start_time_ms, caller=caller)
