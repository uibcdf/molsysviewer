"""`events` are the vertical markers drawn on a trajectory plot.

A list of `{"frame", "label"?, "color"?}` mappings. `frame` is required and is what makes
an event locatable; the other two are decoration.

An event without `frame` does not raise downstream — it is serialised and sent, and the
frontend draws it at an undefined position or drops it silently. That is the failure worth
catching, so it is the only field checked.
"""

from collections.abc import Mapping, Sequence

from molsysviewer._private.exceptions import ArgumentError


def digest_events(events, caller=None):
    if events is None:
        return None
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence):
        raise ArgumentError("events", value=events, caller=caller,
                            message="expected a list of event mappings")
    for event in events:
        if not isinstance(event, Mapping) or "frame" not in event:
            raise ArgumentError(
                "events",
                value=event,
                caller=caller,
                message="every event needs a `frame`; without it there is nowhere to draw",
            )
    return list(events)
