"""The bare element names accepted by `view.get`, resolved against its `element` argument.

`view.get(element='group', name=True)` asks for `group_name`, and the same `name` asks for
`atom_name` when the element is an atom. One table per element states exactly which bare
names that element accepts.

**The tables are MolSysMT's own, re-scoped to this caller.** `view.get` forwards to
`msm.get`, so the set of real `(element, bare name)` combinations is theirs to define, and
re-emitting their tables here means the two cannot disagree. They are written out rather
than generated from an `{element}_{name}` template because several combinations do not
exist — there is no `atom_order`, `chain_order` or `bond_name` — and a template would
accept them, producing an attribute name nothing defines and an error much further
downstream.

If this import ever fails, that is the correct outcome: a silent fallback would drop the
aliases and turn `element='group', name=True` back into the error it used to raise.
"""

from argdigest import AliasTable

from molsysmt._private.argdigest.normalization.get_element_names import (
    TABLES as _MOLSYSMT_TABLES,
)

#: The viewer method that forwards to `msm.get` with `skip_digestion=True`.
_GET_CALLER = 'molsysviewer.viewer.get'

TABLES = [
    AliasTable(
        applies_to=_GET_CALLER,
        when=dict(table.when) if table.when else None,
        aliases=dict(table.aliases),
        description=table.description,
    )
    for table in _MOLSYSMT_TABLES
]
