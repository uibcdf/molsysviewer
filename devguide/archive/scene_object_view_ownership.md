---
summary: Scene operations accept objects belonging to another view
issue: uibcdf/molsysviewer#212
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [scene,layers,regions]
guard: tests/test_public_api_hardening.py::test_foreign_handles_cannot_change_either_scene
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Scene operations accept objects belonging to another view

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

layer.attach(foreign_shape) changes the other view and leaves the target layer empty. Region union accepts another view's local atom indices and UID.

## How

Validate current handle and owning view at the operation boundary, including digestion bypass. Complete layer membership operations for Regions through the region owner.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

A reusable private validator enforces the current owning view before membership, boolean operands or camera focus use a handle. The guard checks two real systems, all three boolean operations, layer attachment and camera focus with digestion enabled and bypassed, and compares both unchanged scene states. Regions now attach/detach through their existing membership owner.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
