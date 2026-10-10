---
summary: new_view with an empty selection hides Whole before failing
issue: uibcdf/molsysviewer#210
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [factory,selection]
guard: tests/test_new_view.py::test_new_view_all_mode_warns_and_keeps_whole_visible_for_empty_selection
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# new_view with an empty selection hides Whole before failing

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

new_view(system, selection="atom_index<0", load_mode="all") raises after hiding Whole instead of warning and retaining the baseline.

## How

The factory still checks the removed view.select route; the mock-only guard retains that retired method. Resolve against view.whole before visibility changes and guard with a real demo.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

The factory resolves through Whole before hiding it. The guard uses a real dialanine view and asserts the empty-selection warning, visible Whole and absence of a spurious region. Nonempty provenance and invalid-query ordering are covered in the same module.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
