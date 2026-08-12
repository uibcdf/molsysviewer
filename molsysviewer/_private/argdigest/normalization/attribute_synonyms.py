"""The attribute synonyms, scoped to the viewer methods that take attribute names.

`molsysmt.attribute._attribute_synonyms` is the source of truth; this points at it rather
than copying, so the two cannot drift apart.

**The scope is not incidental**, in either direction.

*Too wide* renames arguments that are not attribute names: `atom_indices` is a synonym
here and a real argument with its own digester almost everywhere else, so a global table
would turn it into `atom_index`, which nothing declares. Measured by doing it: **132 tests
fail**; the same mistake broke 76 in MolSysMT.

*Too narrow* leaves a caller with no rename at all, which is what the mechanism this
replaced did to every one of them. The condition that decides membership is structural,
not a matter of taste: **a method that digests its arguments here and then forwards
`**kwargs` onward with `skip_digestion=True`** is the last layer that can rename them —
nothing downstream will digest them again. `Region` and `Whole` have that shape too, and
were missed on the first pass; `region.get(element='group', index=True)` raised
`KeyError` exactly as `view.get` had.

`test_argument_name_normalization.py` re-derives this list from the source and fails if a
method acquires that shape without appearing here, because the failure is silent
otherwise. `Whole.get` deliberately does *not* appear: it is a pure forwarder that passes
`skip_digestion` through rather than forcing it, so `view.get` digests on its behalf.
"""

from argdigest import AliasTable

from molsysmt.attribute import _attribute_synonyms

#: Digest here, forward with `skip_digestion=True`: the last chance to rename.
_ATTRIBUTE_TAKING_CALLERS = (
    'molsysviewer.viewer.get',
    'molsysviewer.viewer.contains',
    'molsysviewer.viewer.is_composed_of',
    'molsysviewer.regions.get',
    'molsysviewer.regions.contains',
    'molsysviewer.regions.is_composed_of',
    'molsysviewer.whole.contains',
    'molsysviewer.whole.is_composed_of',
)

TABLES = [
    AliasTable(
        applies_to=caller,
        aliases=dict(_attribute_synonyms),
        description='plural and anatomical synonyms of the canonical attribute names',
    )
    for caller in _ATTRIBUTE_TAKING_CALLERS
]
