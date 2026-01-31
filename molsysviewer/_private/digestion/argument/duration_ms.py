from molsysviewer._private.exceptions import ArgumentError
from molsysmt import pyunitwizard as puw


def digest_duration_ms(duration_ms, caller=None):
    if duration_ms is None:
        return duration_ms
    if puw.is_quantity(duration_ms):
        return puw.standardize(duration_ms)
    if isinstance(duration_ms, (int, float, str)):
        return duration_ms
    raise ArgumentError("duration_ms", value=duration_ms, caller=caller, message=None)
