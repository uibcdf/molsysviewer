---
summary: Object focus has incompatible signatures and accepts retired references
issue: uibcdf/molsysviewer#213
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [camera,scene]
guard: tests/test_public_api_hardening.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Object focus has incompatible signatures and accepts retired references

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

camera.focus_on_object fails for annotations and passes unsupported duration to Interactions. Deleted interaction handles and deleted regions supplied to camera.focus_region still permit focus.

## How

Complete annotation focus, align InteractionSet focus arguments, and reject retired or foreign references before camera commands. Retain typed tag disambiguation and explicit quantity conversion.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

Annotation and InteractionSet focus use current physical geometry, duration and padding. The module compares direct focus with camera dispatch under nm and angstrom output standards, checks explicit wire quantities, and rejects deleted interaction/annotation handles and retired regions without emitting camera changes or clearing redo.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
