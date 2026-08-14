"""The bare element names accepted by `view.get`, resolved against its `element` argument.

`view.get(element='group', name=True)` asks for `group_name`, and the same `name` asks for
`atom_name` when the element is an atom. One table per element states exactly which bare
names that element accepts.

**The tables are MolSysMT's own public plain data, re-scoped to this caller.** `view.get`
forwards to `msm.get`, so the set of real `(element, bare name)` combinations is theirs
to define. MolSysMT explicitly enumerates those combinations rather than generating a
Cartesian product that would admit nonexistent attributes.

If this import ever fails, that is the correct outcome: a silent fallback would drop the
aliases and turn `element='group', name=True` back into the error it used to raise.
"""

from argdigest import AliasTable
from molsysmt.attribute import get_argument_aliases

#: The `get`-shaped methods that digest here and forward with `skip_digestion=True`.
#: `Whole.get` is absent on purpose — it forwards `skip_digestion` through instead of
#: forcing it, so `view.get` digests on its behalf and already has these tables.
_GET_CALLERS = (
    'molsysviewer.viewer.get',
    'molsysviewer.regions.get',
)

_ELEMENT_ALIASES = get_argument_aliases()['element_attribute_aliases']

TABLES = [
    AliasTable(
        applies_to=caller,
        when={'element': element},
        aliases=aliases,
    )
    for caller in _GET_CALLERS
    for element, aliases in _ELEMENT_ALIASES.items()
]
