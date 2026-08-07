from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw


def digest_duration_ms(duration_ms, caller=None):
    if duration_ms is None:
        return duration_ms
    if puw.is_quantity(duration_ms):
        return puw.standardize(duration_ms)
    if isinstance(duration_ms, (int, float)):
        return puw.quantity(duration_ms, "ms", standardized=True)
    if isinstance(duration_ms, str):
        try:
            value = float(duration_ms)
        except ValueError:
            return duration_ms
        return puw.quantity(value, "ms", standardized=True)
    raise ArgumentError("duration_ms", value=duration_ms, caller=caller, message=None)
