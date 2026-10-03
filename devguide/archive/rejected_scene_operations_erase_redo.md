---
summary: Rejected scene operations erase redo without changing the scene
issue: uibcdf/molsysviewer#123
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: medium
verification: reproduced
area: [history, api]
guard: tests/test_scene_integrity.py::TestHistoryCommit::test_rejected_operations_and_noops_preserve_redo
normative:
blocked_by: []
supersedes: []
---

# Rejected scene operations erase redo without changing the scene

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

A validation failure after undo destroys the redo branch:

```python
import molsysviewer as msv
view = msv.new_view(msv.demo["dialanine"].molsys)
view.regions.add(atom_indices=[0, 1], tag="A")
view.regions.add(atom_indices=[2, 3], tag="B")
view.history.undo()
assert view.history.can_redo()
try:
    view.regions.add(atom_indices=[0], tag="A")
except ValueError:
    pass
assert view.history.can_redo()  # fails in the reviewed implementation
```

## How

`SceneHistory._begin_operation` appends the pre-operation snapshot and clears redo before validation/mutation. The decorator always ends the operation in `finally` and does not distinguish failure or an unchanged scene.

## Why

A rejected action must not consume successful prior work. This affects Python calls and Studio actions that use the same public methods.

## Acceptance

Commit a history branch only when the outer operation succeeds and changes reproducible scene state. Preserve undo/redo entries and byte accounting for validation failures and no-op calls. Retain one checkpoint for composite operations, continuous-gesture coalescing, byte budgets and explicit invalidation on molecular edits. Guards must execute a subsequent redo and verify the restored content, not merely the button state.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

History stages a pre-operation snapshot and commits it only after a successful scene mutation. Rejected operations, no-ops and high-water counters alone do not clear redo. Coalescing keys are recorded only for actual committed changes. This is a history guarantee, not rollback of arbitrary partially applied mutations; public operations validate before writing.

The guard creates redo, attempts a duplicate-tag creation and an already-visible show operation, checks unchanged undo/redo, then verifies redo restores the intended color. Disabling the scene-change comparison makes the no-op assertion fail. The coalescing test now uses two real scene changes instead of counting a no-op as an undo step.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
