---
summary: Decide the unit contract of attribute values used for colouring and regions.
issue: uibcdf/molsysviewer#98
status: resolved
opened: 2026-09-24
closed: 2026-10-01
verification: measured
area: [colors, units, regions]
guard: tests/test_scalar_color_units.py
normative: devguide/units_and_quantities.md
blocked_by: []
supersedes: []
---

# Unit contract of scalar colors

## What

The original issue found quantity stripping in the values digester and the
whole/region attribute paths. Relative automatic scales cancel the unit, but
an explicit numeric range can silently compare different physical magnitudes.
This is the remaining support-library boundary under `uibcdf/molsysviewer#110`.

## How

Accept unit-free numeric data and physical quantity arrays. Preserve quantities
through ArgDigest and attribute extraction until scalar normalization. Physical
values with an explicit range require a quantity vector or two compatible scalar
quantities; convert the bounds explicitly to the data's unit. Auto ranges come
from the data itself. Dimensionless quantities, including percentages, normalize
explicitly to dimensionless magnitudes and retain numeric-range compatibility.
Never infer physical units from bare bounds or the active session policy.

The canvas whole/region inputs retain unit-bearing range strings for Python and
PyUnitWizard. Plain numeric pairs remain numeric; malformed input must reach
validation rather than silently selecting an automatic range.

## Why

B-factors expressed in nm squared or angstrom squared must yield identical colors
for physically equivalent ranges, regardless of the application's unit policy.
Colors persisted in scene state are already unit-free RGB integers, so history
and import/export preserve the resolved visual result.

## What was refuted

Rejecting all quantities would make native physical attributes unusable for
normal scalar visualization. Inferring a unit for numeric bounds would preserve
the original ambiguity. The current region surface has no scoring-threshold API;
this decision applies to the implemented scalar-color range and does not create
an additional scientific computation API.

## Evidence and acceptance

Twenty-one real tests pass, including different units and non-default policy,
quantity bounds, incompatible or ambiguous inputs, real demo whole/region values
and native B-factor attributes, undo/redo and state replay, and failure without
scene/history mutation and the actual canvas action handlers. The final focused
run with the public ArgDigest checks passes 24 tests; 76 existing color/unit
checks also passed before the final canvas guards were added.

The single complete source run outside the sandbox returned exit 1:
2,480 passed, 23 skipped, one failed. Its only failure was an existing B-factor
test supplying bare bounds to a physical attribute. That fixture now supplies
explicit angstrom-squared bounds, and the affected module passes in the final
focused run. The complete suite was not repeated; no new complete pass is claimed.

The TypeScript runtime rebuild passes. Native Node 24.11.1 executes and passes
all 296 JS tests, including three range-input guards, outside the sandbox. Inside
the sandbox, worker isolation reported only a file-level test; the explicit
no-isolation invocation executed the same 296 cases successfully. The file-level
result is not counted as suite validation.

## Resolution

Resolved. `devguide/units_and_quantities.md` owns the durable contract.
`tests/test_scalar_color_units.py` fails if quantity stripping, incompatible or
ambiguous ranges, policy-dependent colors, or scene/history mutation returns.
This closes the remaining support-library boundary in `uibcdf/molsysviewer#110`.
The implementation is verified in the working tree; publication and an immutable
1.0 candidate require their own qualification.
