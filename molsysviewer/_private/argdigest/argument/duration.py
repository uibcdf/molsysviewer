"""`duration` is how long a camera transition takes, as a time with its units written.

Explicit units, like every length in this package and for the same reason: `duration=2`
cannot be told from two seconds by anyone reading the call, and it would silently become
two milliseconds. The alias `duration_ms` is where a bare number is unambiguous, because
its name carries the unit, and the message below points there.

That is a deliberate disagreement between the two, not an oversight: they take the same
values everywhere except the one place where one of them names its unit and the other
does not (uibcdf/molsysviewer#86).
"""

from .._quantity import digest_quantity

_MESSAGE = (" A duration requires explicit units (e.g. \"250 ms\" or "
            "puw.quantity(250, 'ms')); a bare number is not accepted, because nothing "
            "in it says whether 2 means two seconds or two milliseconds. Pass "
            "duration_ms=250 if milliseconds are what you mean.")


def digest_duration(duration, caller=None):
    if duration is None:
        return None
    return digest_quantity(duration, "duration", {"[T]": 1}, caller=caller,
                           message=_MESSAGE)
