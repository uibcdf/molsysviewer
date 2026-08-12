"""`callback` is the callable a user registers for an interaction or frame event.

It is checked here because the alternative is a failure that arrives much later and in the
wrong place. `on_hover` only appends to a list; nothing calls the object until the browser
sends an event, so registering a non-callable succeeds, and the `TypeError` surfaces
during a mouse move, inside the event dispatch, with a traceback that names the dispatcher
rather than the registration that caused it.

**Arity is deliberately not checked.** Every callback receives exactly one argument — the
event dict — so a one-parameter signature is the intent, but a bound method, a
`functools.partial`, a `*args` sink and a callable object are all legitimate and all
report their parameters differently. Rejecting on arity would refuse working code; the
docstrings state the contract, and the dispatcher's own `TypeError` is the honest report
if a user ignores it.

`off_*` takes the same argument, so it is digested identically: removing something that
was never registerable is worth refusing at the seam too.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_callback(callback, caller=None):
    if callable(callback):
        return callback
    raise ArgumentError(
        "callback",
        value=callback,
        caller=caller,
        message="an event callback must be callable; it receives the event dict",
    )
