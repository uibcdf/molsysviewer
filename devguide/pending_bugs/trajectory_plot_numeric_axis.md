---
summary: Trajectory plot x coordinates and nonfinite values have inconsistent rendering semantics
issue: uibcdf/molsysviewer#150
status: partial
opened: 2026-10-03
closed:
severity: medium
verification: measured
area: [trajectory, plot, serialization]
guard: tests/test_design_review_closure.py::test_nonfinite_plot_values_are_refused_before_mutation
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Trajectory plot x coordinates and nonfinite values have inconsistent rendering semantics

**Reported:** 2026-10-03, final pre-1.0 design review and principal-maintainer authorization.

## What

The Python API calls x an x-axis coordinate, but the frontend positions all samples uniformly by frame and only uses x for readout. NaN/infinity reach plot/state serialization without a defined missing-data policy.

## How

Inspected trajectory_plot.py normalization/import validation and trajectory-plot-overlay.ts geometry/seeking. Nonconsecutive or repeated frame extraction also requires deterministic seeking at repeated x coordinates.

## Why

Provide a truthful numeric plot axis with frame identity retained and reject unsupported nonfinite data before mutation. Missing or unevaluated interaction counts must not silently become zero.

## Acceptance

Guards for irregular/nonmonotonic/repeated numeric x, playhead/event/seeking consistency and rejection of nonfinite values during API calls and state import. Keep missing-data series a separate contract.

## What was refuted

Source inspection is recorded separately from runtime evidence. No new regression run is claimed at opening.

## Resolution

Implemented in the preserved working tree and locally qualified on 2026-10-03. Integration into a committed supported candidate remains pending. No closure or final release qualification is claimed.

Optional numeric x determines all sample/event/playhead positions and nearest-sample seeking. Nonmonotonic/repeated x retains local frame order. Ties prefer the current frame if it is a nearest candidate, otherwise the earliest candidate. Normalization/state import reject NaN/infinity before mutation; finite extremes and constant data use scaled axis fractions. Range calculation is cached so rendering is linear, not quadratic. Coverage/missing-data series remain a separate provider-dependent contract.

Evidence: `devguide/final_design_closure_20261003.json` and its named test/browser artifacts.

## Reviewed source integration — 2026-10-03

The accumulated source is reviewed, committed and pushed in `0dea171d`.
The final source regression passes 2,805 tests with 23 explicit skips in
`molsyssuite@uibcdf_3.14`; Ruff, TypeScript and runtime rebuild pass.
Earlier installed/browser observations retain their original inputs. This
internal integration used the existing deferred CI route and does not certify
an exact hosted or published-provider candidate. The report remains partial
for its existing supported-artifact/release qualification. See
[`integration_review_20261003.md`](../integration_review_20261003.md).
