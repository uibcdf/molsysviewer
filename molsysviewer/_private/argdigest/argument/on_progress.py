import inspect

from molsysviewer._private.exceptions import ArgumentError


def digest_on_progress(on_progress, caller=None):
    if on_progress is not None and (
        not callable(on_progress)
        or inspect.iscoroutinefunction(on_progress)
        or inspect.iscoroutinefunction(getattr(on_progress, "__call__", None))
    ):
        raise ArgumentError(
            "on_progress", value=on_progress, caller=caller, message="expected a synchronous callback or None"
        )
    return on_progress
