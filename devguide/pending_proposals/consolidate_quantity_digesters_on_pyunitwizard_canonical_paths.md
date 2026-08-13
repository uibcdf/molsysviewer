---
summary: Consolidate quantity digesters on PyUnitWizard canonical paths.
issue: uibcdf/molsysviewer#33
status: open
opened: 2026-08-13
closed:
verification: inspected
area: [argdigest, performance, units]
guard:
normative:
blocked_by: []
supersedes: []
---

# Consolidate quantity digesters on PyUnitWizard canonical paths

**Reported:** 2026-08-13, while propagating PyUnitWizard's completed cheap-canonicity
work through MolSysSuite consumers.
**Status:** Open. The shared length helper is normative, but legacy digesters have not
been audited against it.

## What

Audit MolSysViewer's physical-magnitude digesters and consolidate compatible ones on
the existing `digest_length_quantity()` boundary and PyUnitWizard's canonical
normalization paths.

The existing units policy already requires `puw.ensure_quantity()` through the shared
helper for ordinary length arguments. The proposal closes the gap between that policy
and older digesters that still implement their own `check()`, `get_unit()`, and
`standardize()` sequences.

## How

Inventory production quantity digesters and group them by semantic contract: scalar
length, coordinate-like array, box, time, energy, dimensionless vector, or special
union/list input. Migrate plain length arguments to `digest_length_quantity()` when its
shape, optionality, and error behavior match exactly.

For array and interactive paths, use `ensure_quantity()` as the default boundary.
Introduce `has_unit()` only after a representative benchmark shows remaining fixed
overhead and only when the local code must also normalize shape or dtype. Preserve the
viewer `ArgumentError` translation and use `get_value(..., to_unit=...,
value_type=..., dtype=...)` at the Mol* wire boundary.

## Why

The normative policy says not to hand-roll
`parse → is_quantity → check → standardize → raise`, yet source inspection finds many
legacy digesters that predate the shared helper. That duplication can drift in accepted
inputs, exception types, canonical units, and performance.

PyUnitWizard's optimized `ensure_quantity()` means the shared implementation now has a
cheap canonical path. Consolidation can therefore improve consistency without placing
backend-specific unit logic in MolSysViewer.

## What is measured and what is assumed

Measured upstream and in a representative MolSysViewer length digester: canonical
inputs benefit from the optimized PyUnitWizard boundary, while non-canonical inputs
retain validation and conversion.

Assumed: some remaining legacy digesters are both compatible with the shared helper
and frequent enough for the change to matter. The audit must distinguish those from
specialized or cold paths before implementation.

## What was refuted

- A blanket replacement of all quantity digesters is unsafe. Boxes, coordinates,
  union-valued arguments, and dimensionless directions have different contracts.
- Bare numbers must not become an optimization fallback; the units policy explicitly
  rejects them.
- `has_unit() is False` is not a dimensionality check. Untrusted non-matches and
  undecidable inputs return to the general validation route.
- `skip_digestion=True` is not a unit fast path. It remains restricted to internal
  delegation after every argument invariant has already been established.

## Scope and exclusions

In scope are Python argument digesters and Python-to-Mol* magnitude extraction. Out of
scope are frontend payload-schema changes, a new default unit for bare values, global
unit-configuration policy, and unrelated rendering performance.

## Acceptance criteria

- Production magnitude digesters are inventoried and classified by semantic contract.
- Plain length digesters use the shared helper when behavior is identical.
- Specialized migrations have canonical, compatible non-canonical, incompatible-unit,
  shape, batch, and local-error regression coverage as applicable.
- Representative interactive paths are benchmarked before adding explicit canonical
  branches.
- Wire serialization converts explicitly to angstroms with PyUnitWizard extraction
  controls rather than manual array/scalar wrapping.
- Focused tests and the normal MolSysViewer full-suite gate pass.
- Durable local rules are incorporated into `devguide/units_and_quantities.md`; the
  canonical API rules remain in `PYUNITWIZARD_GUIDE.md`.

## Dependencies and risks

The work depends on the PyUnitWizard version documented by the synchronized guide. The
main risks are changing local exception types, accidentally accepting bare magnitudes,
and treating dimensionless direction vectors as lengths.

