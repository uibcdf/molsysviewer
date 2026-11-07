---
summary: Trajectory plot navigation changes the canvas without updating Python structure state.
issue: uibcdf/molsysviewer#314
status: partial
opened: 2026-11-06
closed:
severity: high
verification: reproduced
area: [trajectory, api, embedding]
guard: molsysviewer/js/tests/e2e/trajectory-plot.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Plot navigation and Python structure authority

## What

An actual Jupyter calculation/adoption workflow clicks a point in a core
trajectory plot, then observes a different current-structure state in Python.
The browser confirms local structure 1 and draws that playhead; a subsequent
kernel assertion `view.player.index == 1` fails. The initial R3 campaign did not
capture the Python value. The subsequent minimal causal regression establishes
that Python remains at index 2 after the actual plotted sample-1 click.

The core plot callback in `molsysviewer/js/src/managers/viewer-controller.ts`
calls `trajectory.setTrajectoryFrame` locally. The ordinary slider additionally
sends a trajectory intent through the Python authority bridge. Source inspection
identifies that omitted route. A real browser/Python regression now reproduces
the omission and verifies the repair through the retained owner, rather than
only inspecting source text.

## How

Viewer checkpoint d33e97bc and executable/runtime source 239c8dd7, named Python
3.14.7 environment, explicit PyUnitWizard 02d0015 source, actual Jupyter/AnyWidget/
Mol* and headless Chrome. The independent addon working tree extends owner PR
#543 over af8eabcd8 with conformation tables and deliberate core plot adoption;
that extension is uncommitted and not presented as owner-integrated evidence.

Three distinct bundled pentalanine conformations [0,8,3] supply the current
MolSys's local structure axis. Independent coordinate oracles check raw/optimal
RMSD, gyration and RMSF, including repeated selections. The R3 campaign passes
sixteen steps through numerical tables, actual plot geometry/labels, a genuine
SVG point click, both popup types and retained plots after Clear. Its final
kernel verification fails at the current-index assertion; prior coordinate,
chemistry and managed-revision assertions pass. The later assertions in that
cell have not executed and are not claimed as passing.

Private evidence: `msv-conformation-jupyter-r3-20261106/full-failure.json`,
`failure-dom.txt`, screenshots and server/kernel records. R1 selected a toolbar
icon along with the chart SVG; R2 tried to click through overlapping Studio.
Those are separate test-driver attempts, corrected by a precise graph selector
and ordinary Studio collapse without force-clicking. Neither is the causal
explanation of the R3 Python disagreement.

All four pages of the board were acquired through the owning gh helper: 284
issues, 312 records including PRs. Closed #291 concerns Python-origin callback
dispatch, #312 measurement summaries, #143 card lifetime and #150 numeric axes.
None reports this plot-origin authority omission. The preserved acquisition is
`msv-plot-navigation-board-20261106.json`.

## Why

Current-structure calculations, callbacks, periodic boxes, interaction/measurement
summaries and saved view state must follow deliberate plot navigation. A correct
rendered curve and local playhead alone cannot establish that agreement.
This core behavior blocks complete acceptance of the new conformation workflow;
it is not a reason to weaken its Python assertion or remove that task family.

## Required repair and receiving

Reuse the existing user-intent/authority path used by trajectory controls.
Keep raw programmatic/render projections distinct to avoid feedback loops.
Retain standalone/static local navigation and a single playback authority.
Verify actual browser input against Python index/public callbacks and mirrored
views, including repeated selections, source/popup navigation and retained plots.
Use distinct molecular structures and check coordinates/analyses are unchanged.
Re-run the actual Jupyter workflow after the causal fix, with a precise Python
index diagnostic and explicit acknowledgement semantics.

Add a real browser-to-Python regression in the core lane. Select an addressable
guard through the repository's reporting profiles before closure; a Python test
constructing a correct event does not protect the TypeScript omission. Keep
visible Qt/human, hosted and installed qualification separate. Both 1.0 and all
candidate/tag/package publication operations remain paused.

Related consumer work: uibcdf/molsysmt#421 / PR #543 and Viewer #264.

## Causal repair and current validation

The working correction forwards plot-origin navigation through the existing
`trajectorySyncToAuthority` intent, matching the ordinary slider. Raw render
projections remain silent. The causal red run observes Python index 2 instead
of 1 before the production change; the green run clicks actual SVG points and
checks the retained Python index, deduplicated public callbacks, every atom's
coordinates in two rendered conformations, source-to-popup navigation and
Python-to-both-canvas projection. The actual exported self-contained HTML keeps
working independently and does not change the notebook authority. The exact
core browser entry above is registered by the bounded local guard profile.

Private red/green evidence is retained in
`msv-plot-authority-red-receipt-20261106.json`,
`msv-plot-authority-red-r3-20261106.log` and
`msv-plot-authority-static-final-20261106.log`. Two earlier attempts corrected
test plumbing (the shared browser context and the protocol envelope); neither
is presented as a product failure or the causal red result.

The complete Jupyter R4 workflow passes all 17 checks, including deliberate
source-plot sample 1 and canvas-popup sample 2 navigation. The final kernel
cell verifies index 2, callbacks `[1, 2]`, retained separate plots and unchanged
molecular data. All 4,768 selected input hashes, both heads and both worktree
statuses remain unchanged during that run. Its receipt is
`msv-conformation-jupyter-r4-receipt-20261106.json`. The Jupyter debugger error
is also present in the plain baseline notebook; that environmental observation
is retained separately from product assertions.

Affected Python/lifecycle/reporting checks pass 380 tests with 43 legacy-H5MSM
warnings. The JavaScript unit entry passes with no skips.

The original complete core attempt failed at 43/44: its popup-origin intent had
not necessarily arrived when the test drained the host queue. The receiving
helper now observes that actual intent at the host transport before draining
queued Python responses. It retains ordinary SVG input and all original Python,
callback and physical-coordinate assertions; it does not poll until Python
happens to agree or force a click through another panel.

The affected guard passes after that correction. One new complete core run
passes **44/44 suites**, exit 0 in 1,367.664 s, with all **4,305** selected
executable/test/provider inputs unchanged. A documentation-only commit changed
HEAD during the run; no unchanged-HEAD claim is made. The run excludes the
separately prepared A1/A3 and A6 patches. See the
[receiving receipt](../trajectory_plot_authority_receiving_20261106.json).
The original failing attempt remains evidence of the earlier test/run outcome.

Reviewed source is delivered in `25061d9e99baf07fa0dcb4021897958a226f0152`;
the applicable consolidated hosted checkpoint remains pending and this record
is partial. Commits use the maintainer-authorized
`[skip ci]` route. These are controlled source checks, not installed-package
qualification or postponed human Jupyter/visible-Qt acceptance.
