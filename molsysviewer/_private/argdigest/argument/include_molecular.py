"""`include_molecular` decides whether a popup snapshot carries the molecular generation.

A strict boolean, and this one is load-bearing rather than cosmetic: `False` means the
generation is being delivered out of band on the data plane, so a snapshot that says
`False` when the caller meant `True` produces a popup with a scene and no structure. The
two arrive by different routes, which is exactly the case where a silently coerced value
is hardest to trace back.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_include_molecular(include_molecular, caller=None):
    if isinstance(include_molecular, bool):
        return include_molecular
    raise ArgumentError(
        "include_molecular",
        value=include_molecular,
        caller=caller,
        message="expected True or False; False means the structure travels out of band",
    )
