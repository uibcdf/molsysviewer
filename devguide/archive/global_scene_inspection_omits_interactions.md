---
summary: Global scene inspection omits the Interactions domain
issue: uibcdf/molsysviewer#124
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: medium
verification: reproduced
area: [api, interactions, inspection]
guard: tests/test_scene_integrity.py::test_scene_inventory_includes_interactions_and_layer_counts
normative:
blocked_by: []
supersedes: []
---

# Global scene inspection omits the Interactions domain

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

Source inspection in the final design review found that `view.info()` omits tagged Interactions sets and the layer member breakdown does not count interaction members, even though they are canonical scene objects and appear in their own manager. The defect is inspected, not yet reproduced through the public output.

## How

`viewer/molsysmt_interface.py:_viewer_info_records` enumerates existing domains and counts shape/annotation/measurement/region members explicitly, but has no interaction branch. The corresponding summary is similarly maintained field by field.

## Why

The public scene inventory must agree with scene managers and Studio. Analyses and visual sets are different entities and must not be conflated into a single count.

## Acceptance

Include tagged interaction sets in global scene inspection with analysis reference, layer, visibility and appropriate frame/status metadata. Include interaction members in layer breakdowns; keep scientific analyses separate from visual objects. Exercise public dictionary/dataframe/styler outputs on real demos and check consistency with manager records and typed layer membership. This completes the inspection integration of #114.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

Global scene summary and dictionary/dataframe/styler inspection now include typed Interactions rows, their named-analysis reference, layer and effective visibility. Layer member breakdowns count interactions. Named scientific analyses remain distinct from visual sets.

The guard creates a real demo analysis and visual set, asserts the typed global row and separate analysis names, checks all three public output formats and the layer member count, then hides the layer and checks effective visibility. This protects an output-producing integration; the engineering mutation rule does not require deleting its producer.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
