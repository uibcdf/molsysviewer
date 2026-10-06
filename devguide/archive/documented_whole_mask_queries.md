---
summary: Documented Whole mask examples still pass query strings to an index-only argument
issue: uibcdf/molsysviewer#160
status: resolved
opened: 2026-10-04
closed: 2026-10-06
severity: medium
verification: reproduced
area: [documentation, selection]
guard: tests/test_documented_whole_masks.py::test_documented_whole_masks_resolve_expressions_before_refining
normative:
blocked_by: []
supersedes: []
---

# Documented Whole mask examples disagree with the public index-only contract

## What

Hosted notebook run `37191306553`, on commit `c598d2f2`, executes all 24
notebooks and fails `docs/content/user/molecular_system/get.ipynb`:

```python
protein_ca = view.whole.select(
    selection='molecule_type=="protein"', mask='atom_name=="CA"'
)
```

The notebook explicitly states that both selection and mask accept expressions,
and later passes `mask='group_name=="PHE"'` to `view.whole.get`. The accepted
public contract restricts mask to indices; the observed failure is
`ArgumentError` from the mask digester. The opening issue abbreviates the query
strings; the exact executed literals are recorded here.

## How

The public mask digester intentionally accepts all or explicit indices. Resolve
the refinement through the existing public selection owner and pass its indices,
or express the combined condition in `selection`. Update the example and prose
consistently, then execute the notebook rather than relying on Sphinx rendering.

## Why

This is a visible documentation promise that disagrees with the accepted API.
The principal maintainer explicitly places public documentation after functional
closure; this report records the work for that final block. Do not reintroduce
string masks or skip the notebook to make the gate pass.

## What was refuted

The same hosted run also fails the Interactions notebook with `backend_required`:
its published MolSysMT provider lacks the experimental API. That is the existing
published-provider gate in uibcdf/molsysviewer#114/#140, not this selection-example
defect. The Studio #158/#159 changes do not alter the Python mask contract.

## Resolution

The notebook now resolves CA and PHE expressions with `view.whole.select`
and supplies their atom indices as masks. The PHE example refines the full
protein CA selection instead of silently limiting it to the first five atoms.
The actual example cells run against the real bundled 181L demo in
`tests/test_documented_whole_masks.py`; the guard checks the exact combined
protein/CA result and nonempty PHE refinement. All 13 code cells of the
corrected notebook execute, as do all 25 documented notebooks against the
fixed source provider. The strict Sphinx build passes. The full Python run has 2,883 passes,
23 skips and one clean-checkout link failure caused by the new reports not yet
being in the Git index. Staging those reports makes all four devguide-link
checks pass. The full suite is not repeated. Native/source workflow evidence
is retained separately; the two published-provider tutorial failures do not
reopen the corrected mask contract.
