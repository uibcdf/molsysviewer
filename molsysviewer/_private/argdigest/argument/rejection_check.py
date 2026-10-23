"""A provider token reader can qualify preservation of nested native state."""

from molsysviewer._private.exceptions import ArgumentError


def digest_rejection_check(rejection_check, caller=None):
    if rejection_check is None or callable(rejection_check):
        return rejection_check
    raise ArgumentError("rejection_check", value=rejection_check, caller=caller, message="expected a callable or None")
