"""`scope_atom_indices` limits `expand_values_to_atoms` to part of the system.

The same rule as any atom index list, delegated to `digest_atom_indices` rather than
restated: it accepts the forms that digester accepts, including `"all"`, and refuses what
it refuses.

`None` is valid and means the whole system. It is a distinct argument name rather than a
reuse of `atom_indices` because the same call also carries element-level `values`, and
naming it `atom_indices` would read as "the atoms these values belong to", which is the
opposite of what it does.
"""

from .atom_indices import digest_atom_indices


def digest_scope_atom_indices(scope_atom_indices, caller=None):
    if scope_atom_indices is None:
        return None
    return digest_atom_indices(scope_atom_indices, caller=caller)
