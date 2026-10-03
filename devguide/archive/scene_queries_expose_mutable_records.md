---
summary: Scene records queries expose mutable nested canonical state
issue: uibcdf/molsysviewer#121
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: high
verification: reproduced
area: [api, scene]
guard: tests/test_scene_integrity.py::TestDetachedReads::test_nested_records_are_detached
normative:
blocked_by: []
supersedes: []
---

# Scene records queries expose mutable nested canonical state

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

Public queries return shallow copies that retain mutable nested state:

```python
import molsysviewer as msv
view = msv.new_view(msv.demo["dialanine"].molsys)
view.shapes.add_sphere(tag="s", color=0x00FF00)
view.annotations.add(text="original", atom_indices=[0], tag="a")
view.shapes.records()[0]["options"]["color"] = 0x0000FF
view.annotations.records()[0]["options"]["text"] = "changed through records"
```

The canonical replay color/text changed. Shapes and Annotations were reproduced; Measurements uses the same shallow-copy pattern by source inspection.

## How

Their `records()` implementations use `[dict(record) for record in history]`. Nested options, anchors and lists remain shared. Related metadata-query boundaries need a bounded audit for the same aliasing mechanism.

## Why

A read can bypass validation, undo, frontend synchronization and provenance. The documented scene model depends on mutations passing through public mutators.

## Acceptance

Return detached or immutable scene query records, including nested metadata and indices. Mutating returned containers must not affect subsequent queries, state or history. Preserve intentionally shared immutable numeric arrays in scientific results; do not materialize entire trajectories to repair small scene metadata.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

Scene records now detach nested data for Shapes, Annotations, Measurements and Selections. Layer metadata and camera-offset reports are detached. Whole/region representation parameters, style summaries and figure recipe summaries also detach nested mutable metadata. Scientific coordinate/result arrays are not copied wholesale by this metadata repair.

The guard clears nested options in returned records and asserts that canonical exported state stays identical. Removing the Shapes deep copy makes it fail. Additional regressions cover nested layer metadata, selection indices, representation parameters, style summaries and annotation offsets.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
