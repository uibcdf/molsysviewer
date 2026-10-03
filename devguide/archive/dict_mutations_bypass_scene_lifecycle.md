---
summary: Dict mutations bypass scene manager lifecycle and leave orphaned members
issue: uibcdf/molsysviewer#122
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: high
verification: reproduced
area: [api, layers, regions]
guard: tests/test_scene_integrity.py::TestRegistryLifecycle::test_raw_mutations_are_rejected_without_scene_changes
normative:
blocked_by: []
supersedes: []
---

# Dict mutations bypass scene manager lifecycle and leave orphaned members

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

`LayersManager` and `RegionsManager` expose inherited dictionary mutations that bypass scene lifecycle:

```python
import molsysviewer as msv
view = msv.new_view(msv.demo["dialanine"].molsys)
view.layers.add("L")
view.shapes.add_sphere(tag="member", layer_tag="L")
view.layers.pop("L")
assert not view.layers.contains("L")
assert view.shapes["member"].layer_tag == "L"
```

This orphaned membership was reproduced. `view.regions.clear()` also inherits raw `dict.clear` and omits region deletion messages and reconciliation (source inspection).

## How

Both public managers are mutable dict subclasses. `pop`, `popitem`, `update`, item assignment/deletion and related operations are not constrained to validated manager operations. Regions reserves semantic bulk deletion as `delete_all`, leaving `clear` as a raw registry mutation.

## Why

Ordinary mapping operations can leave Python, Mol*, layer membership, recipe dependencies and undo inconsistent. Dictionary access is public and documented, so this cannot be treated as unannounced private mutation.

## Acceptance

Keep key access and iteration convenient while constraining mutation to validated scene operations. Provide coherent `clear` semantics; unsafe inherited mutation must either be refused before changes or route through the full public lifecycle. Update internal registry mutation sites explicitly, document the pre-1.0 contract change, and guard public mapping behavior plus ordinary add/delete/rename/restore paths.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

Region and layer managers retain dictionary reads but reject assignment, deletion, update, pop, popitem, setdefault and in-place union. Public clear/delete methods use the scene lifecycle. Trusted internal registry writes are explicit dictionary operations.

The guard checks seven raw mutation routes in both managers and asserts rejection with unchanged canonical state. Restoring raw __setitem__ makes it fail. The clear regression verifies region color cleanup and restoration through undo. Earlier tests that injected fake objects/raw registry entries were migrated to real demo objects and manager construction.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
