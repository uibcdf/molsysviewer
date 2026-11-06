from numbers import Integral

from ...exceptions import ArgumentError


def digest_expected_revision(expected_revision, caller=None):
    if expected_revision is None:
        return None
    if isinstance(expected_revision, Integral) and not isinstance(expected_revision, bool) and expected_revision >= 0:
        return int(expected_revision)
    raise ArgumentError("expected_revision", value=expected_revision, caller=caller)
