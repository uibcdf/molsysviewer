---
summary: Diagnose the hosted popup context-menu timeout after fullscreen controls receiving.
issue: uibcdf/molsysviewer#305
status: resolved
opened: 2026-11-06
closed: 2026-11-16
severity: medium
verification: reproduced
area: [ci, popup, context-menu]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/interaction_gestures_and_menus.md
blocked_by: []
supersedes: []
---

# Hosted popup context-menu receiving

**Resolved in source — 2026-11-16.** A committed-source matched negative
control reproduces dismissal by unchanged-frame Python playback metadata;
the correction preserves that context and still dismisses it on actual frame
changes, explicit seeks and coordinate/loading changes. Complete hosted
controls and scientific-mirror owners both pass in `43796373853`, source
`e3fefadc` / MolSysMT `4b0b1f8a`, Node 22.23.5. The menu receives real FPS 17
before its visibility assertion; a genuine frame change then closes it.
The original hosted input sequence remains unrecorded. This closes the
evidenced class and C4's bounded source disposition, not an invented exact
history, the failed overall diagnostic, installed or final acceptance. The
[receipt](../residual_four_issues_receiving_20261116.json) retains every scope.

## What

Core E2E run 42206567233, source 63e79096ef3c3414c2fabacf5f44e81e9b475440,
times out waiting for the context menu after the notebook canvas-popup
fullscreen/Studio sequence. The export/controls phase passes. This is an
observed qualification failure, not an established product defect or cause.

## How

`checkNotebookCanvasPopup` right-clicks canvas.x + 30, canvas.y + height - 30
after returning from fullscreen. The existing 30-second wait finds a hidden
menu. Native log: `/tmp/msv-host63-controls-42206567233-failed.log`; hosted
[run](https://github.com/uibcdf/molsysviewer/actions/runs/42206567233).
No failure artifact was emitted. The complete 303-record board acquisition
precedes this report; closed #232/#244/#209 have different mechanisms.

Local receiving with current pending-reader source passes the full
`controls-visibility` entry, including actual Python authority, notebook
bootstrap and scientific Mol* mirror assertions. Hit-target diagnostics show
CANVAS at the tested point. Log:
`/tmp/msv-host63-controls-diagnostic-20261106.log`. No context-menu behavior,
timeout, retry or assertion was changed. This does not reproduce or explain
the hosted failure. The source and environment scopes remain distinct.

## Why / next evidence

Inspect the next applicable hosted gate. If the timeout recurs, capture the
hit element, layout, pointer events and menu state before classifying the
cause. Keep the failed run and local passing evidence separately. Closure
needs an explained disposition and a guard relevant to that cause; a passing
rerun alone is insufficient. The pending-reader implementation is #304 and
does not claim to repair this separate observation.

The next hosted core E2E, 42210858347 on docs checkpoint 6e23f37f (unchanged
pre-reader JS runtime), passes. This confirms non-reproduction in that run,
not a cause or a product correction. Keep the observation open pending an
explained disposition; neither the new reader nor a test retry repairs it.

## Original hosted evidence rechecked — 2026-11-09

Published GH Run Receptor 1.1.1 reacquires the original run and complete native
logs: Core E2E failed, the skipped-commit backlog check was skipped, and no
artifact exists.
The native log records 64 resolutions to the hidden menu during the unchanged
30-second wait. It does not record the event target, pointer sequence or drawn
layout, so it still cannot distinguish failure to open from a subsequent close.
The capture is retained with the current source-pair receiving packet. Its
separate passing Jupyter addon scenarios do not close this controls-visibility
observation. Keep #305 open and receive targeted diagnostics on the next
applicable hosted core checkpoint; do not infer a cause from non-reproduction.

## Failure evidence armed — 2026-11-10

The existing [canvas popup scenario](../../molsysviewer/js/tests/e2e/canvas-popup-scenarios.ts)
now records the hit target, viewport/canvas bounds, capture and bubble pointer
sequence, and changes to the menu's visibility attributes around the same
right-click. On failure, the bounded trace is written to the native test log;
the original wait failure propagates. The original click and success criterion
are unchanged. The observer and its browser handle are released in either case.

`build-273-c4-controls` passes the complete local `controls-visibility` entry,
including the actual Python notebook popup bootstrap, context menu, and native
scientific mirror. It ran in 362.42 s with 2 logical CPUs, a 6 GiB cgroup cap,
zero swap, and 2479.9 MiB peak summed owned RSS. All 24 owned processes retire;
10,895 inputs and the production runtime bundle remain unchanged. This is
new local evidence, not a hosted reproduction or a root-cause disposition.

The separate Chromium control in `probe-274-small-causal-controls` deliberately
opens and immediately closes a menu at the tested canvas point. It verifies
that the original visibility failure still propagates and the trace records
the canvas hit, delivered context-menu event, intermediate open style and
final hidden state. This is a control of the evidence collector, not a
reproduction of the hosted failure. Keep the issue open.

## Current causal class and receiving — 2026-11-16

The controller closes a menu on every trajectory-state publication, including
a playback-option summary that leaves the molecular frame unchanged. A native
empty-canvas control receives one real right-click and then a real Python FPS
summary: 30 becomes 17, frame zero is unchanged, and the menu closes. The
source correction retains context for those metadata publications. Explicit
seeks, loading, clearing, coordinate edits and actual structure changes retain
context invalidation. The real popup guard now checks Python FPS publication
without dismissing the menu, and an actual frame change that does dismiss it.

Current real-pentalanine receiving `944` passes with three structures: the hit
is CANVAS, ordinary pointer-down/contextmenu/up opens the menu, and FPS 17
preserves it at frame zero. All 9,983 selected inputs remain unchanged and all
13 owned processes retire; native exit is zero without a resource stop. This
receives that corrected class, not the original unrecorded hosted sequence.
An exact pre-correction-source molecular comparison and the expanded hosted
diagnostic are prepared. The original `939` popup attempt is interrupted by
global swap; reduced empty-view `943` times out before metadata and lacks the
input trace, so neither is credited as a passing or causal metadata result.
See the [four-issue receipt](../residual_four_issues_receiving_20261116.json).

The exact pre-correction-source comparison is now received in `948`. It
builds 351 Git-verified JavaScript/manifests from committed `9bc3f2f6` using
the same native provider/adapter, and reuses the exact complete pentalanine
fixture bytes from successful corrected `944`. Both receive a CANVAS hit and
frame zero; FPS 17 closes the original menu and preserves the corrected menu.
The original close stack is `applySummary -> updateTrajectoryState ->
onTrajectoryState -> contextMenu.close`. The negative-control checker expects
and preserves that original Node assertion failure. Preparation failure `946`
lacked two manifests and never ran the browser; `947` supplies those exact
committed inputs. This establishes the corrected metadata dismissal class,
while the historical hosted event ordering remains unrecorded.

Before dispatch, source review also aligns context invalidation with the
existing settled-follower no-op optimization: a same-frame metadata envelope
may arrive through the mirror even though the molecular model is unchanged.
The handler now exposes that same predicate to the dispatcher; this does not
add a new projection-skipping rule. Explicit seeks, disagreeing models and
in-flight returns retain invalidation/application. Build `951` receives the
runtime, harness, all browser-entry compilation, 491 JavaScript unit cases
without skips/failures and TypeScript. The actual popup metadata/frame guard
remains the hosted prerequisite.


## Hosted preparation outcomes — 2026-11-16

First diagnostic `43786553755` fails workflow preparation; the focused browser
suites do not run and the prolonged pytest command executes zero cases.
Successor `43790196548` passes the audit but the unchanged installed Rust
validator rejects its editable distribution; the new prerequisite fence
correctly skips all browser/Jupyter consumers. Neither receives this issue.
[#399](../pending_bugs/focused_source_diagnostic_preparation.md) owns those corrections; the
[four-issue receipt](../residual_four_issues_receiving_20261116.json) preserves
both failures and the next bounded dispatch independently of product evidence.

In `43791283994` the actual popup menu opens successfully; the new receiving
then waits for an FPS editor absent by design in compact mode. Corrected local
complete entry `959` observes the real popup controller's applied FPS 17 and
frame zero, requires the menu to remain visible, then requires a genuine frame
change to dismiss it. It passes the complete controls/parity entry in 115.67 s.
The exact-source negative metadata control `948` remains paired evidence;
the original hosted event ordering is still unrecorded. The next hosted
diagnostic receives this corrected predicate without changing product input,
mode, deadline or invalidation semantics.
