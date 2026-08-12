"""`state` is the overlay document handed to `import_state`.

Only the shape ArgDigest can judge is judged here: it must be a mapping. Everything that
makes it a *valid* document — `version: 2`, the region dependency graph being acyclic,
operands existing before their dependents — stays in `import_state`, which is the only
place that knows the schema and which already refuses rather than loading half a scene.

Splitting it this way keeps one rule in one place. What this adds is the caller's name on
the failure when someone passes a path where a document was expected, which is the mistake
the two similarly-shaped entry points invite: `load_state(path)` and `import_state(state)`.
"""

from collections.abc import Mapping

from molsysviewer._private.exceptions import ArgumentError


def digest_state(state, caller=None):
    if isinstance(state, Mapping):
        return state
    raise ArgumentError(
        "state",
        value=state,
        caller=caller,
        message="expected the dict from export_state(); for a file, use load_state(path)",
    )
