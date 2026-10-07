---
summary: Trajectory plot x coordinates and nonfinite values have inconsistent rendering semantics
issue: uibcdf/molsysviewer#150
status: resolved
opened: 2026-10-03
closed: 2026-10-07
severity: medium
verification: measured
area: [trajectory, plot, serialization]
guard: tests/test_design_review_closure.py::test_nonfinite_plot_values_are_refused_before_mutation
normative: devguide/scene_contracts.md
blocked_by: []
supersedes: []
---

# Trajectory plot x coordinates and nonfinite values have inconsistent rendering semantics

**Resolved — 2026-10-07:** the published Viewer 0.24.0 build 1 / MolSysMT
0.23.0 ABI3 build 0 pair is qualified. Fresh installed finite-value and lifecycle
guards, numeric geometry/seeking units and executable guide examples pass.
Earlier dated sections retain their original scope.

**Current qualification — 2026-10-06:** implementation is committed and
integrated in Viewer 0.24.0 build 1 with MolSysMT 0.23.0 ABI3 build 0. All
sixteen installed staging cells and 39 hosted core browser suites pass;
canonical-source Python 3.14 integration passes on all three native hosts,
with 25 documented notebooks passing on Linux. This report remains partial
for its public-provider/release qualification; staging evidence does not
close that gate. See the [current handoff](../checkpoints.md#resume-in-one-page)
and [exact candidate receipt](../stabilization_024_preparation_20261006.json).
Earlier dated sections retain their original scope.

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

## Published qualification and closure — 2026-10-07

The earlier public-provider/release blocker is complete: both fixed packages,
Releases and version-specific Zenodo records are public, and independent
verification establishes all sixteen public installed cells in `37587631519`.
The plot Python owner, numeric TypeScript owner and its unit/browser guards
match the published Viewer producer `1a4c97a5` byte for byte. No additional plot
implementation change is required.

Twelve fresh checks run through the isolated installed-science qualifier on the
original promoted files: six NaN/positive-infinity/negative-infinity refusals
across series/x and six real-system lifecycle cases. They check API/state-import
refusal before mutation, strict JSON serialization, nonconsecutive/repeated
structure extraction with remapped event markers, state/session/copy and
unchanged structure-axis validation. Seven direct Node unit cases pass, including
irregular/nonmonotonic/repeated x, shared sample/event/playhead positions,
current-frame/earliest-frame tie resolution and finite extreme/constant SVG
geometry. This unit DOM observation remains separate from real browser evidence.

The real Mol* plot browser guard checks nonuniform horizontal spacing and
coincident repeated values; complete core `37680239149` and exact-source pair
`37680239068` already pass on the unchanged plot sources. The public guide now
states local frame identity, click ties and finite input semantics. Its new
three-structure example executes against the installed public pair; Sphinx
passes with warnings treated as errors. Missing-data/coverage series retain
their separate future contract.

The fresh local full-source attempt is failure, not qualification: 22 cases
cannot bind loopback sockets/start Chromium or complete Qt graphics inside the
restricted executor. This does not replace the passing hosted science/core
and public-artifact evidence. The companion #149 applied-style correction is a
separate source follow-up and has not replaced the published package.

[Checks, artifact identity and preserved verdicts](../styles_plot_closure_20261007.json).
Final 1.0 candidate recertification remains mandatory in the release plan.
