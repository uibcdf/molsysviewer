---
summary: Measurements.add re-enables digestion inside an explicit bypass
issue: uibcdf/molsysviewer#215
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [measurements,argdigest]
guard: tests/test_public_api_hardening.py::test_general_measurement_constructor_preserves_explicit_bypass
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Measurements.add re-enables digestion inside an explicit bypass

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

The general measurements.add entrypoint repeats digestion and differs from the specific add_distance entrypoint when skip_digestion=True.

## How

Forward normalized arguments using the explicit bypass to the selected public constructor; preserve scientific and lifecycle invariants.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

The already validated general constructor delegates with skip_digestion=True. The guard compares real geometry and stored style with the named constructor while passing a normalized immutable style mapping under explicit bypass.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
