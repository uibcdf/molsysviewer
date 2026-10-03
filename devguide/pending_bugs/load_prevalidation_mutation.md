---
summary: Replacement loading and system edit validation can mutate the scene before failing
issue: uibcdf/molsysviewer#148
status: partial
opened: 2026-10-03
closed:
severity: high
verification: measured
area: [load, live_edit]
guard: tests/test_design_review_closure.py::test_invalid_replacement_conversion_preserves_scene
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Replacement loading and system edit validation can mutate the scene before failing

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

load(mode='replace') clears the viewer before MolSysMT conversion succeeds. apply_system_edit(load_blocks='append') checks required appended_n_atoms only after replacing the system and rebuilding the scene.

## How

Inspected viewer/load.py and viewer/core.py. Conversion and joint argument validation need preparation before Viewer-owned mutations.

## Why

A failed load or invalid edit request must preserve the current scene. Existing external edits remain the caller's responsibility; no rollback of prior caller mutations is promised.

## Acceptance

Real-demo guards checking system identity, overlays, history and outgoing messages remain unchanged on invalid replacement/conversion and missing append accounting.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

The owning loader separates preparation (conversion, selected source maps and scale checks) from commit. Replacement resets only after preparation succeeds. Conditional append accounting is validated before analysis invalidation, assignment and rebuild. These guards protect conversion/argument failures, not a rollback of every renderer or external-provider mutation.

Evidence: `devguide/final_design_closure_20261003.json` and its named test/browser artifacts.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).
