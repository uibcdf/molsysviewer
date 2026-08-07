import numpy as np

from ...exceptions import ArgumentError


def _digest_one_alpha(alpha):
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float, np.number)):
        raise TypeError
    value = float(alpha)
    if not 0.0 <= value <= 1.0:
        raise ValueError
    return value


def digest_alpha(alpha, caller=None):
    """Digest a single opacity in [0, 1], or a batch (sequence) of them."""
    if alpha is None:
        return None
    try:
        if isinstance(alpha, (list, tuple, np.ndarray)):
            return [_digest_one_alpha(a) for a in alpha]
        return _digest_one_alpha(alpha)
    except (TypeError, ValueError) as exc:
        raise ArgumentError("alpha", value=alpha, caller=caller, message=None) from exc
