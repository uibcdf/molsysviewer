"""`endpoint` is correlation and routing metadata on a popup snapshot.

Deliberately unconstrained beyond `None`. The docstring of the only caller states it:
*"it never changes the scientific content of the projection"*. It is an identifier the
transport layer attaches and reads back, and constraining its shape here would couple the
projection to whatever the router currently uses to name a destination.

Declared rather than left undeclared for the usual reason: an undeclared argument warns on
every call, which says nobody has looked at it. This says the opposite.
"""


def digest_endpoint(endpoint, caller=None):
    return endpoint
