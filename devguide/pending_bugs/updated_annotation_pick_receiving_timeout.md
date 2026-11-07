---
summary: Updated annotation GPU pick times out in hosted canvas-popup receiving.
issue: uibcdf/molsysviewer#325
status: active
opened: 2026-11-07
closed:
severity: medium
verification: measured
area: [annotations, picking, popup, ci]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Updated annotation picking in hosted popup receiving

## What

The exact-source Linux receiving guard times out while locating an updated explicit-position annotation in the canvas popup after changing its text. Initial shape picking and the original annotation pick succeed; the later popup pick of `mirror-label` does not return a matching GPU hit within the unchanged 30-second deadline. The underlying product-versus-guard/timing cause is not established.

## Evidence

- Viewer `e4dd58cf0edcb2c3afb2c982ccd50d3899d504ab`, MolSysMT source `46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`, Linux/Python 3.14 source-pair run 42387355324, job 128447461685: `controls-visibility` fails at the final `nativePick(peer, "annotation", "mirror-label", [0,30,0])` after `update-label` and the revised summary. Original source log and native failure are retained.
- The same Viewer’s separate core lane 42387347683 passes 44/44 suites. A later local instrumented controls entry also passes on its separately recorded provider route. Neither pass is a causal repair of the source-pair failure.
- #241 fixed non-pickable text render state and #243 fixed deleted registered references. Both fixes remain present; there is no evidence yet that either original mechanism has returned. #199 concerns a different stale-transform cleanup path.
- Mol* source was inspected at the installed 5.4.1 tag; the external checkout’s current 6.0 development tree is not treated as the running implementation.

## Next action and acceptance

Retain bounded observations of the actual failed GPU query, current camera/viewport, live reference/render-object state and resolved shape owners. Preserve the real pick predicate, post-edit click, selected markers at both endpoints and original deadlines; do not substitute fake loci, force a click or treat non-reproduction as resolution. Use the bounded source-only Linux diagnostic profile to inspect this boundary and the independent live-Jupyter failure without repeating unrelated matrices.

Close after an evidenced cause/fix or an explicitly approved disposition, with relevant actual-browser receiving and original failures retained. This belongs to the Viewer receiving work under #315; no scientific calculation defect, installed qualification, candidate or publication is claimed.


## Bounded diagnostics and local receiving

The guard retains the last actual GPU query's viewport/draw/context-loss
observations, bounded returned owners and current live representation state
only when it fails. The real pick predicate, coordinates, selected markers,
original deadlines and cleanup stay intact. Local complete controls receiving
passes in 198.94 seconds on the separately qualified e119/PUW02d provider route,
with fixed selected driver/runtime bytes and all 17 owned processes closed.
This does not establish the cause or resolve the original hosted failure.
The source-only Linux diagnostic profile repeats just this entry and the
independent live-Jupyter boundary against the exact hosted provider.

The single hosted diagnostic `42395570310`, source `b980adb5` with the exact
original MolSysMT provider, passes the complete controls entry and its revised
label picks/selected markers under the original deadlines. Only passive
diagnostics changed; this is non-reproduction, not a causal product fix. The
independent Jupyter step fails its missing-tool preflight; both facts remain
separate.
