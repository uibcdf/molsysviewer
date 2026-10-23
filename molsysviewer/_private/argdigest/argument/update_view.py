"""The integration update switch accepts an explicit boolean only."""

from molsysviewer._private.exceptions import ArgumentError


def digest_update_view(update_view, caller=None):
    if not isinstance(update_view, bool):
        raise ArgumentError("update_view", value=update_view, caller=caller, message="expected a boolean")
    return update_view
