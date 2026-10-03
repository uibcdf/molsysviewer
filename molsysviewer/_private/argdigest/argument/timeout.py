import math
from numbers import Real

from ...exceptions import ArgumentError


def digest_timeout(timeout, caller=None):
    """The worker wait timeout is a finite positive number of seconds."""
    if isinstance(timeout, Real) and not isinstance(timeout, bool) and math.isfinite(timeout) and timeout > 0:
        return float(timeout)
    raise ArgumentError("timeout", value=timeout, caller=caller)
