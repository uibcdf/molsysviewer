---
summary: Stale scene handles can mutate objects restored by undo or reused tags
issue: uibcdf/molsysviewer#120
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: high
verification: reproduced
area: [scene, identity, history]
guard: tests/test_scene_integrity.py::TestHandleLifetime::test_replaced_handles_cannot_mutate_restored_objects
normative:
blocked_by: []
supersedes: []
---

# Stale scene handles can mutate objects restored by undo or reused tags

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

A retained shape handle from before undo can mutate the replacement object under the same tag:

```python
import molsysviewer as msv
view = msv.new_view(msv.demo["dialanine"].molsys)
s = view.shapes.add_sphere(tag="s", color=0x00FF00)
s.set_color(0xFF0000)
view.history.undo()
current = view.shapes["s"]
assert s is not current
s.set_color(0x0000FF)  # mutates the restored object's replay payload
```

The old handle remained `_active=True` in the reproduced case. Lifetime behavior across clear/reset/import/tag reuse requires the same audit.

## How

Bulk unregister/restore paths replace canonical instances without uniformly invalidating earlier handles. Rich shape mutators resolve replay messages by tag, without checking that the calling handle is the current object. Tag identity alone permits an earlier incarnation to address a replacement.

## Why

User-held Python objects must have an explicit, consistent lifetime. Silent writes to a replacement make visibility, filters, grouping and history unreliable.

## Acceptance

Define and enforce handle validity across undo/redo, clear, import, reset and tag reuse for every affected scene domain. The proposed minimum is explicit invalidation of substituted handles, with callers obtaining the current object through the manager. Stale mutations must fail before altering scene or history; no object may be resurrected or unregister another incarnation. Rebuilds that retain the canonical object must retain its valid handle.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

Handles are checked against the exact registered object lifetime before mutation and history staging. Delete/reset/import retire old objects. Geometry reads and measurement focus refuse retired handles, and section drag controls check lifetime before sending runtime messages. Reacquire handles after undo/import/tag reuse.

The guard holds shape, annotation, measurement, region, layer and selection handles across undo, verifies replacement identities, and asserts rejection without scene or redo changes. Removing the lifetime check makes it fail. The separate section-drag regression asserts that a retired handle sends no message to its replacement.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
