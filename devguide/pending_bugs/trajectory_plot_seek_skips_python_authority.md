---
summary: Trajectory plot navigation changes the canvas without updating Python structure state.
issue: uibcdf/molsysviewer#314
status: active
opened: 2026-11-06
closed:
severity: high
verification: reproduced
area: [trajectory, api, embedding]
guard:
normative:
blocked_by: []
supersedes: []
---

# Plot navigation and Python structure authority

## What

An actual Jupyter calculation/adoption workflow clicks a point in a core
trajectory plot, then observes a different current-structure state in Python.
The browser confirms local structure 1 and draws that playhead; a subsequent
kernel assertion `view.player.index == 1` fails. The exact Python value is not
yet captured. Do not assume it is the prior index 2 without a diagnostic.

The core plot callback in `molsysviewer/js/src/managers/viewer-controller.ts`
calls `trajectory.setTrajectoryFrame` locally. The ordinary slider additionally
sends a trajectory intent through the Python authority bridge. Source inspection
identifies that omitted route; a minimal browser/Python guard must verify the
causal repair rather than only inspecting source text.

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
