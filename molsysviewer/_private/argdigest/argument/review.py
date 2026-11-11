from collections.abc import Mapping

from ...exceptions import ArgumentError


def digest_review(review, caller=None):
    if isinstance(review, Mapping):
        return dict(review)
    raise ArgumentError("review", value=review, caller=caller, message="expected a Movie review dict")
