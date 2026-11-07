---
summary: Trajectory labels hide nonzero values and narrow-offset axes lose numerical precision.
issue: uibcdf/molsysviewer#321
status: partial
opened: 2026-11-07
closed:
severity: medium
verification: reproduced
area: [trajectory-plot, numeric, frontend]
guard: molsysviewer/js/tests/e2e/trajectory-plot.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Numerical reading and geometry of trajectory plots

**B2 — corrected in working source; source receiving passes; delivery and consolidated acceptance pending.** Viewer owns formatting and axis
arithmetic. This is a core visualization defect, not evidence of incorrect
MolSysMT calculations. [#321](https://github.com/uibcdf/molsysviewer/issues/321)
records the scoped work under #315.

## Observation

A real Mol*/Chromium controller renders the public plot/state output of a
pentalanine View with structures `[0, 8, 3]`. The five series below are explicitly
supplied synthetic numeric controls, not scientific detector results.

| Control | Stored input | Actual displayed result |
| --- | --- | --- |
| Small lengths | Y `[0.0001, 0.0002, 0.0005]`, label `Length (nm)` | All three Y readouts are `0.00` |
| Narrow X range | X `[1.0001, 1.0002, 1.0005]` | Both axis limits are `1.00`; all X readouts are `1.00` |
| Equivalent units | PyUnitWizard converts those lengths to `[0.001, 0.002, 0.005]` angstrom | Readouts are `0.00`, `0.00`, `0.01`; unit choice changes which equivalent observations appear zero |
| Signed small values | Values around `1e-8` | Nonzero values become `-0.00` or `0.00` |
| Large common offset | Represented binary64 values `[1e12 + .001, 1e12 + .002, 1e12 + .003]` | Limits/readouts all show `1000000000000.00`; the middle point also has a measurable positioning error |
| Wide finite range | `[-1e308, 0, 1e308]` | Labels remain finite; preserve this overflow control during correction |

For the large-offset case, an independent Decimal oracle on the exact
represented floats places the middle sample at normalized fraction
`0.47058823529411764`. The rendered polyline gives `0.47368421052631576`:
an error of `0.0030959752321981227` of the drawable span, or `1.2260061919504566`
pixels in this fixture. This is a numerical normalization error in addition to
the label-formatting defect. It is not a discrepancy between decimal literals
and their binary64 representation: the oracle starts from those actual floats.

Raw public plot records survive a Python state round trip unchanged. All five
browser controls complete with no page errors, and all eight selected
source/fixture/harness inputs remain unchanged. Probe native exit is **0**
because it records these defects; it does not mean fixed-code acceptance.

## Source and reproduction scope

`formatValue` in `molsysviewer/js/src/ui/trajectory-plot-overlay.ts` applies two
fixed decimals to noninteger values. That turns nonzero observations into
apparent zero and can give distinct limits the same label. `axisFraction`
normalizes large-offset operands before subtracting them, adding cancellation
error for a narrow span. Its wide-range overflow protection is still required.

The plot owner is unchanged from Viewer
`9a783d500a756210e70e11946552c4afbe5fe936`; separate #319 work is present.
The environment is the explicit routine Python 3.14 interpreter, controlled
MolSysMT `e119953435a25c72e9a65b7428f74b1c2430b4f1` and the recorded
PyUnitWizard `02d0015` snapshot. The browser uses the built real Mol* harness,
not a fake DOM or a test-constructed plot geometry.

Private originals under `.pytest_cache/robustness-20261106` retain
`B2-precision-fixture.py`, `B2-precision-probe.mjs`, the actual payload,
observations, source hashes and native receipts. The initial fixture attempt
failed before browser execution because its loader call omitted the required
`label`; that driver-only traceback and original script are retained separately.
After correcting that argument, the actual fixture/browser run completes.

The public reproduction starts with:

```python
import molsysviewer as msv

with msv.demo["pentalanine"] as original:
    view = original.extract(structure_indices=[0, 8, 3])

view.trajectory_plot.show(
    {"control": [0.0001, 0.0002, 0.0005]},
    x=[1.0001, 1.0002, 1.0005],
    x_label="Numeric control",
    y_label="Length (nm)",
    title="Precision control",
    tag="precision",
)
view
```

## Duplicate review and required correction

The current complete inventory has four pages and 319 unique issue/PR records,
including closed work. Closed #150 received numeric X positions, frame identity
and nonfinite rejection; it does not receive this formatting/narrow-span defect.
Closed #312 concerns stale structure-specific measurement summaries, not
numeric formatting. #315 already identifies this scope as B2.

Use readable significant digits/scientific notation with the supplied units.
Keep nonzero/signed values interpretable, distinguish unequal limits and offer
access to the complete value where display rounding is useful. Do not invent
scientific uncertainty or change stored observations to match a display.
Correct the narrow-span arithmetic while retaining finite wide-range geometry,
actual X coordinates and deterministic frame/seeking identity.

Acceptance needs actual browser labels/readouts and geometry for tiny, signed,
large, narrow-offset and cross-unit-equivalent controls, with independent
oracles on represented floats. Receive save/restore and popup behavior and
retain the existing irregular/repeated/nonfinite contracts. A fixed-code
regression, applicable source receiving and normal closeout are still pending.

## Working correction and receiving limits

The working correction subtracts represented values before dividing when the
span is finite, retaining the scaled overflow fallback. Axis-aware significant
digits and scientific notation preserve nonzero readings, distinguish unequal
limits by numerical value across notation thresholds, and expose roundtrip
raw values through titles/accessibility labels. Eleven isolated unit cases pass;
the broader canonical unit entry and TypeScript also pass before the later
notation-threshold refinement. The new actual browser fixtures have fifteen
independent Decimal controls, including subnormal, threshold and near-maximum
finite cases. These are not yet passing browser acceptance.

The first sandbox browser attempt exits 1 before a page because Chrome sockets
are denied. The actual-host entry then passes its existing public-authority,
physical-frame, popup and static-output checks, but exits 1 before new numerical
assertions: `width=650` exposes the separate public digestion defect #322.
Its 12 selected receiving inputs remain unchanged. The fixture retains that
requested width and now surfaces backend errors before inspecting records;
it does not bypass the broken public argument. Correction of #322 and fresh
actual numerical/browser receiving remain required.

The later full actual browser entry **passes with native exit 0 in 91.12 s**.
It receives all fifteen Decimal/binary64 controls, full-value title/ARIA/keyboard
access, real source/popup frame changes and state-file restoration after
perturbation. Existing irregular/repeated/nonfinite, static output, navigation
and title contracts remain in the entry. All 17 declared selected inputs remain
unchanged. Chromium uses Swiftshader; this is not a visible/native GPU claim.
The [source receipt](../trajectory_plot_precision_receiving_20261107.json)
separates these results from the retained earlier failures. Source delivery,
consolidated acceptance and normal closeout remain pending.

A subsequent run with the newer shared camera runtime exits **1** after the
source precision/state controls and earlier navigation contracts pass. At the
first `large-offset` case in the popup-stage endpoint loop, the SVG points are
finite but normalization divides by an axis-reference bounding-box width of
zero. The guard did not retain the exact endpoint or that bounding box. This
does not yet establish an incorrect scientific value or plotted coordinate;
capture the SVG geometry and ancestor visibility before changing the product
or the numerical oracle. All 3,947 selected inputs remain unchanged and all 17
owned process identities exit. The earlier passing run retains its own inputs;
the current shared-runtime receiving remains pending.
