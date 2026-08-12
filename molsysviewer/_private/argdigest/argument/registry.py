"""`registry` is the add-on registry a reference add-on is registered into.

`None` is the common case and means the global `molsysviewer.addons`. A value is for tests
and for embedders that keep their own registry, so what matters is that it can act as one:
this is a duck-type check on `register`, not an isinstance against
`GlobalAddonsRegistry`.

Checking the type would be the tighter-looking choice and the wrong one. The add-on
contract is that an embedder may supply their own host surface, and demanding our class
would refuse a legitimate one while gaining nothing — the very next line calls `register`.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_registry(registry, caller=None):
    if registry is None:
        return None
    if callable(getattr(registry, "register", None)):
        return registry
    raise ArgumentError(
        "registry",
        value=registry,
        caller=caller,
        message="an add-on registry is anything with a `register` method",
    )
