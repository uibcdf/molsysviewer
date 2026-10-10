---
summary: Annotations ignores accepted syntax and unsupported kind
issue: uibcdf/molsysviewer#211
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [annotations,selection]
guard: tests/test_public_api_hardening.py::test_annotation_arguments_are_honored_before_mutation
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Annotations ignores accepted syntax and unsupported kind

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

annotations.add(..., syntax="MDTraj", selection="resid 0") parses as MolSysMT despite a valid provider selection. An unsupported kind silently creates a label.

## How

The anchor resolver hardcodes MolSysMT and add does not check kind. Respect declared syntax, align reanchoring, and reject unsupported kinds before mutation.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

Creation and reanchoring honor the selection syntax. The guard compares MDTraj anchors with the canonical selection owner and asserts unsupported kind rejection leaves the full scene unchanged.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
