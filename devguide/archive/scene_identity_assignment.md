---
summary: Direct identity assignment desynchronizes handles and registries
issue: uibcdf/molsysviewer#216
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [scene,selection,layers]
guard: tests/test_public_api_hardening.py
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Direct identity assignment desynchronizes handles and registries

**Reported:** 2026-10-10, final public API review with the principal maintainer.

## What

selection.tag = "changed" leaves the registry under the prior name and retires the returned handle. Scene-object identity and grouping fields expose similar raw writes.

## How

Expose read-only identity/membership properties; migrate internal writes to private lifecycle operations. Validate manager-driven rename, grouping, undo, import and restored handle access.

The same review found that `Region.rename()` accepted an occupied tag and could
overwrite its registry entry. Validate through the existing region tag owner;
renaming to the current tag remains a no-op.

## Why

These routes are user-visible before 1.0. The closed inventory proves argument
coverage, but does not prove behavioral parity or handle identity correctness.
Reproductions use real dialanine/pentalanine and the native scientific backend
in `molsyssuite@uibcdf_3.14`; they are source evidence, not package qualification.

## What was refuted

The 23 existing inventory/entrypoint/documented-symbol tests pass. Their success
does not cover this behavior. No MolSysMT functionality change is required.

## Resolution

Public identity fields are read-only; internal owners write private fields. The module asserts raw identity writes fail without changing the scene, supported rename/grouping survive Undo/Redo/import, and duplicate region rename refuses to overwrite a registry entry. Region.set_tag delegates to the validated rename owner.

Related real-system regression: 376 passed. Full-suite and executor limitations
are retained in `devguide/public_api_review_20261010.md`; these are source guards,
not installed-artifact qualification.
