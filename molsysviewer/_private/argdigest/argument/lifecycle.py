"""`lifecycle` are the enable/disable hooks registered alongside an add-on.

`None` is the common case: most add-ons have nothing to do when they are switched on. When
given it is an `AddonLifecycleSpec`, and the type check is deliberate here where
`registry` gets a duck-type — a lifecycle is our own declared shape, not a surface an
embedder supplies, and accepting anything with the right attribute names would let a
half-built spec register hooks that are never called.
"""

from molsysviewer._private.exceptions import ArgumentError


def digest_lifecycle(lifecycle, caller=None):
    if lifecycle is None:
        return None
    from molsysviewer.addons import AddonLifecycleSpec

    if isinstance(lifecycle, AddonLifecycleSpec):
        return lifecycle
    raise ArgumentError(
        "lifecycle",
        value=lifecycle,
        caller=caller,
        message="expected an AddonLifecycleSpec",
    )
