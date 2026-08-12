"""`default` is the sentinel a lookup returns when nothing was found.

Its whole purpose is to be whatever the caller wants back — `None`, a `Layer`, an empty
list, a raising sentinel — so there is nothing here to validate. It is declared rather
than left undeclared because the two states are not the same: an undeclared argument
warns on every call under `STRICTNESS = "warn"`, which says "nobody has looked at this".
This says the opposite, on purpose.

Used by `view.layers.get` alone. If a second `default` ever appears meaning something
constrained, that constraint belongs on *its* caller, not here — this must stay the
identity it is.
"""


def digest_default(default, caller=None):
    return default
