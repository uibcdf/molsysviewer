---
summary: Saved-selection labels expand their anchor to a whole group
issue: uibcdf/molsysviewer#214
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [selection,annotations]
guard: tests/test_public_api_hardening.py::test_saved_selection_label_retains_exact_atoms_without_deprecated_routes
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Saved-selection labels expand their anchor to a whole group

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

A saved selection [0,1] creates a label anchored to [0,1,2,3,4,5]; multiple groups are refused although the equivalent active selection works.

## How

Selection.add_label delegates through deprecated group_index rather than the saved atom set. Delegate to annotations.add with the exact indices.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

Selection.add_label delegates exact atom indices to annotations.add. The guard checks partial and multiple groups, identical anchor indices and absence of deprecation warnings.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
