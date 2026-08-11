"""The attribute synonyms, scoped to the viewer methods that take attribute names.

`molsysmt.attribute._attribute_synonyms` is the source of truth; this points at it rather
than copying, so the two cannot drift apart.

**The scope is not incidental.** These synonyms rename attribute *names*, and only three
viewer methods take attribute names as keywords. Everywhere else the same words are
ordinary parameters: `atom_indices` is a real argument of several viewer calls and has its
own digester, and a global table would rename it to `atom_index`, which nothing declares.
Declaring them globally breaks **132 tests here**, measured by doing it; the same mistake
broke 76 in MolSysMT. It is the obvious simplification and it is wrong.
"""

from argdigest import AliasTable

from molsysmt.attribute import _attribute_synonyms

#: The viewer methods whose keywords are attribute names. All three forward to MolSysMT
#: with `skip_digestion=True`, so this is the only place the rename can happen.
_ATTRIBUTE_TAKING_CALLERS = (
    'molsysviewer.viewer.get',
    'molsysviewer.viewer.contains',
    'molsysviewer.viewer.is_composed_of',
)

TABLES = [
    AliasTable(
        applies_to=caller,
        aliases=dict(_attribute_synonyms),
        description='plural and anatomical synonyms of the canonical attribute names',
    )
    for caller in _ATTRIBUTE_TAKING_CALLERS
]
