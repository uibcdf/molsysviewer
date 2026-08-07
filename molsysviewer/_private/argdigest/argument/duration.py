from molsysviewer._private.exceptions import ArgumentError
from molsysviewer._pyunitwizard import puw


def digest_duration(duration, caller=None):
    if duration is None:
        return duration
    if puw.is_quantity(duration):
        return puw.standardize(duration)
    if isinstance(duration, (int, float, str)):
        return duration
    raise ArgumentError("duration", value=duration, caller=caller, message=None)
