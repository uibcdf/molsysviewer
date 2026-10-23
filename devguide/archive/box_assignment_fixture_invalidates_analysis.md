---
summary: Box-assignment guard invalidates its own analysis during setup with current MolSysMT.
issue: uibcdf/molsysviewer#263
status: resolved
opened: 2026-10-22
closed: 2026-10-22
severity: low
verification: reproduced
area: [testing, interactions, box]
guard: tests/test_box_assignment.py::test_subset_invalidates_only_edited_frames_and_refreshes_visible_edges
normative:
blocked_by: []
supersedes: []
---

# Box-assignment fixture invalidates its own fresh analysis

**Reported:** 2026-10-22, independently reproduced before the #262 implementation
on clean Viewer `d96b073f23247e25cd42c95af545b6d20e7fa982` with the development
provider. The issue holds the original reproduction and observed coverage.
**Status:** resolved test-fixture defect; scientific invalidation is unchanged.

## What

The subset-edit guard expected evaluated structures `[0, 1, 2]` in its original
analysis, but setup had already cleared coverage before the operation under test:

```text
python -m pytest --receptor=llm tests/test_box_assignment.py::test_subset_invalidates_only_edited_frames_and_refreshes_visible_edges
actual evaluated_structure_indices: []
expected: [0, 1, 2]
```

## How

The shared fixture attached fresh synthetic evidence, then the test called the
public scientific box setter. That setter correctly invalidated geometric
coverage. The preparation contradicted its own comment about initializing the
cell before attaching analysis.

## Why

The test no longer exercised selective invalidation starting from a fully
evaluated analysis and failed in the consumer core suite. Suppressing scientific
invalidation would conceal the fixture error rather than protect the product.

## What was refuted

This is not a regression introduced by the molecular-load history change or the
addon read facade: the same failure was reproduced on the clean earlier parent.
No private provider storage patch, weaker coverage assertion, dependency upgrade
or automatic recalculation is needed.

## Resolution

The fixture accepts an initialized-cell variant and sets that cell before creating
the view and attaching the synthetic analysis. Only this test selects the variant;
the other cell-assignment tests retain their empty-box starting state. The test
keeps the assertions for immutable prior coverage, surviving evaluation of
structure 1 after editing `[2, 0]`, updated box edges and subsequent box removal.
Its redundant private source-binding cache reset is removed.

The complete focused file passes 44 tests with the real provider in
`molsyssuite@uibcdf_3.14`. This is consumer source-contract evidence, not a newly
qualified installed package pair. The subsequent global check is recorded with
the integration delivery rather than retrospectively changing earlier receipts.

## Provenance

2026-10-22, Python 3.14 environment `molsyssuite@uibcdf_3.14`, Viewer parent
`e37ff48673279115f1958a821a72e9287bd65563`, MolSysMT source parent
`fa2f3aa9232372e5fa7db8bbf4ebd9e2ad481056` with separately preserved concurrent
provider work. The focused command was
`python -m pytest --receptor=llm tests/test_box_assignment.py -x`.
