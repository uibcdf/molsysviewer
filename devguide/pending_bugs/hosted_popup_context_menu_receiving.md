---
summary: Diagnose the hosted popup context-menu timeout after fullscreen controls receiving.
issue: uibcdf/molsysviewer#305
status: open
opened: 2026-11-06
closed:
severity: medium
verification: upstream
area: [ci, popup, context-menu]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Hosted popup context-menu receiving

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
