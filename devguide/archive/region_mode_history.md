---
summary: Region mode changes must participate in scene history
issue: uibcdf/molsysviewer#220
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [public-api, scene]
guard: tests/test_public_api_followup.py::test_region_mode_is_undoable_and_invalid_changes_preserve_redo
normative:
blocked_by: []
supersedes: []
---

# Region mode changes must participate in scene history

**Reported:** 2026-10-10, final API review with real dialanine systems.

## What

After history.clear(), region.mode="dynamic" changes exported scene state but history.can_undo() stays false.

## How

Add digested Region.set_mode and route assignment through it; retain private automatic transitions. Implementation owner: `molsysviewer/regions.py and the mode digester`.

## Why

Public queries, history and introspection must agree with scene contracts before 1.0.

## What was refuted

Provider atom-scoped system queries work; this is Viewer ownership/delegation. Existing mutation guards do not protect undecorated read paths. No package qualification or scientific stability claim follows from these local checks.

## Resolution

Implemented the public boundary in molsysviewer/regions.py and the mode digester. Guard `tests/test_public_api_followup.py::test_region_mode_is_undoable_and_invalid_changes_preserve_redo` passes on real dialanine data. The complete related execution passes 310 cases. The single full run reports 3056 passed, 9 failed and 23 skipped; eight failures are known experimental Qt host probes, and the ninth is the superseded whole-system count test. After updating that policy assertion, its tools module passes 14 cases. No second full execution or globally green claim. The source follow-up and receipt retain the evidence; 0.25.0 remains unfrozen and publication paused.
