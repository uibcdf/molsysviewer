---
summary: import_state replays a region's atom indices instead of re-evaluating its recipe
issue: uibcdf/molsysviewer#66
status: resolved
opened: 2026-09-01
closed: 2026-09-01
severity: high
verification: reproduced
area: [state, regions]
guard: tests/test_state_structure_identity.py::test_a_region_is_re_evaluated_from_its_recipe_not_replayed_from_its_atoms
normative:
blocked_by: []
supersedes: []
---

# A region arrived on a new system still holding the old one's atoms

**Reported:** 2026-09-01, while designing the structure-identity slice of #38. The slice
started from the premise that a state document has no way to survive a change of system,
which turned out to be false for regions: the means had been in the document all along and
import did not use it.

## What

Contract R says a region *is* its recipe, not the atoms the recipe happened to select. The
state document has carried that recipe since v2. `import_state` never used it.

```python
src = demo["181L"]                                   # 1441 atoms
src.regions.add(selection="atom_name=='CA'", tag="cas")
doc = src.export_state()

tgt = demo["dialanine"]                              # 22 atoms
tgt.import_state(doc)
tgt.regions.info("cas")
# n_atoms: 162, atom_indices max: 1281
```

162 atoms, indices reaching 1281, on a system of 22. The recipe was in the same record,
unread:

```
provenance: {'kind': 'query', 'expression': "atom_name=='CA'", 'syntax': 'MolSysMT'}
```

## How

`molsysviewer/viewer/state.py`, `_restore_region_v2`. The re-evaluation machinery already
existed — `Region._is_reevaluable_provenance` and `_evaluate_region_provenance` — and was
reached only when the record carried no `atom_indices`. When indices were present they won,
whatever system they had been written for.

So this was never a missing capability. It was a precedence: the cached result outranked the
definition.

## Why

A region carries a representation, so it draws. Here it drew over indices addressing atoms
past the end of the loaded system — or, on a system of the same size, the wrong atoms with
nothing out of range to give it away. Contract S7 names that outcome the worst this codebase
produces: not an error, not a visible gap, but a scene that looks right.

The defect was reachable from the documented workflow (`export_state` on one system,
`import_state` on another) with no warning of any kind.

## What was refuted

**That refusing the import is the fix.** The first implementation of #38's slice 1 raised
when the saved and loaded atom counts differed. It was wrong in both directions: too strict,
because loading a state onto a related structure is a capability that Contract S7 has a test
for, and too weak, because the counts match in the case that actually hurts — a system of
the same size whose indices address different atoms. It also broke that S7 test, which is
what exposed the collision.

**That the region case needed new machinery.** It needed a precedence change, four lines.
The work that remained was for the objects that genuinely have no recipe.

## Resolution

Fixed in `4ac9c612`, as part of #38's structure-identity slice.

`_restore_region_v2` now re-evaluates the recipe whenever the loaded system is not the one
the document was written from — decided by the `structure` fingerprint the same commit
introduced. When the fingerprint matches, the indices are still used unchanged, so the
common path is untouched.

Objects that hold atoms without a recipe (annotations, measurements, saved selections) are
handled by the same commit through per-atom identity rather than recipes; they are not part
of this defect, which is specifically about a recipe that existed and was ignored.

Verified against the reproduction above: the region now resolves to the single CA that
dialanine actually has. Guard: `test_a_region_is_re_evaluated_from_its_recipe_not_replayed_from_its_atoms`,
mutation-verified — disabling the re-evaluation turns it red.
