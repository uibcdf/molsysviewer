"""`ref` is an entity reference: the identity carried alongside a geometry payload.

Either an `EntityRef` or the mapping it serialises to, which is what makes a payload
round-trip through JSON without the class travelling with it. Anything else produces a
payload whose `kind` and `entity_id` are missing, and the loss surfaces in the frontend as
an anonymous shape rather than as an error here.
"""

from collections.abc import Mapping

from molsysviewer._private.exceptions import ArgumentError


def digest_ref(ref, caller=None):
    if ref is None:
        return None
    if isinstance(ref, Mapping):
        return ref
    if hasattr(ref, "kind") and hasattr(ref, "entity_id"):
        return ref
    raise ArgumentError(
        "ref",
        value=ref,
        caller=caller,
        message="expected an EntityRef or the mapping it serialises to",
    )
