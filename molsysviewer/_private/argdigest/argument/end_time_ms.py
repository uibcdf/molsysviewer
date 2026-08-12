"""`end_time_ms` is a point on the movie timeline, in milliseconds.

One of a family of four that share a rule; it lives in `_shared.check_milliseconds`.
"""

from .._shared import check_milliseconds


def digest_end_time_ms(end_time_ms, caller=None):
    return check_milliseconds("end_time_ms", end_time_ms, caller=caller)
