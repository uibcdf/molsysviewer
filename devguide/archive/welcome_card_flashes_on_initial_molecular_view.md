---
summary: Welcome card flashes before the initial molecular view is rendered
issue: uibcdf/molsysviewer#247
status: resolved
opened: 2026-10-20
closed: 2026-10-20
severity: low
verification: measured
area: [loading, ui, lifecycle]
guard: molsysviewer/js/tests/e2e/initial-welcome.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Welcome card flashes before the initial molecular view is rendered

**Reported:** 2026-10-20, first observation in Diego and Liliana's pre-1.0
TcTIM / PDB 1TCD exploratory dogfooding. The transient is a human observation
on the notebook canvas before successful molecular rendering. Automated
receiving of the correction now covers the complete widget startup and first
rendered frame; the opening report initially contained source inspection only.

## What

```python
import molsysviewer as msv
view = msv.new_view('1TCD')
view
```

Before the molecular system appears, the Welcome card is visible for a fraction
of a second. This view has molecular input from creation and should not present
the intentionally empty-session entry card during initial loading.

Welcome remains appropriate for genuinely empty molecular views and the intended
standalone entry state. This report does not ask to remove those entry paths.

## How

At issue opening, `molsysviewer/js/src/managers/viewer-controller.ts` called
`updateWelcomeState(true)` from the constructor, with `structureLoadPending`
initially false. The `hasInitialStructures` option suppressed Welcome only when
the caller marked `isInitPhase`; ordinary updates used the empty-state branch.
`molsysviewer/js/src/index.ts` read the widget's `initial_messages` before
controller creation and replayed those messages afterward.

The initial inspection lead was incomplete: real TcTIM construction publishes
an empty `initial_messages` trait. Its molecular projection arrives only after
the frontend sends `ready`, so `parseInitialTrajectoryInfo` cannot declare an
initial system at all. The early empty-state updates therefore insert Welcome
before the first loader is invoked. The reporter's exact loaded frontend bytes
remain unrecorded; automated correction receiving has its own runtime identity.

Review source is `df4bf477e921c2b64d9bf32ff1418cc6863ae9fe`; synchronized
`cfa7d4117b00028ff74c0c0ab2860f7fdc25abd8` adds governance only. Neither is asserted
to identify the reporter's loaded runtime bundle.

## Why

The first visible state should reflect the supplied molecular input. A Welcome
flash suggests an empty canvas during a workflow that is already loading a
system. This is a low-severity pre-1.0 usability defect.

Acceptance requires a real widget/browser observation installed before
controller creation through the first molecular rendering, recording zero
Welcome DOM insertions for an initial molecular system. Cover the reported
`new_view('1TCD')` workflow and applicable initial replay transports. Preserve
genuinely empty views, intended standalone entry behavior, explicit clearing,
diagnosed loading failure, shape-only scenes and panel-only endpoint rules.
Keep progressive additions/replacements protected by their existing guard.

## What was refuted

The closed [uibcdf/molsysviewer#164](https://github.com/uibcdf/molsysviewer/issues/164)
corrected a different lifecycle interval: progressive rebuilding after a system
is visible. Its `composite-load.e2e.ts::checkProgressiveWelcome` observer starts
after applying `fixture.progressive_wire[0]` and does not observe widget creation
or first replay. The [archived report](../archive/welcome_card_flashes_during_system_rebuild.md)
retains that completed scope. This observation does not establish regression of
the previously corrected progressive path.

The closed [uibcdf/molsysviewer#240](https://github.com/uibcdf/molsysviewer/issues/240)
concerns Welcome and workspace access for shape-only views; it is not this
initial molecular-load report. No existing issue specifically covering this
initialization interval was found in the open/closed issue search.

An arbitrary delay or an assertion only after loading would not demonstrate the
required absence of the transient.

## Implementation and receiving — 2026-10-20

The widget synchronizes a small `has_molecular_system` hint when Python prepares
or replays a molecular projection, and clears it on reset. The controller enters
the existing pending-load state before panel setup if either that hint or
initial molecular messages declare a system. Ordinary loader success/failure
and explicit clearing retain their existing cleanup. No coordinates are added
to the initial widget traits and no timing delay is introduced.

The new `initial-welcome.e2e.ts` guard mounts the real widget bootstrap and live
Python authority, observes every Welcome insertion before controller creation,
and waits for Mol* `didDraw` with real TcTIM representations. Both binary and
JSON paths pass with bundled TcTIM and with the reporter's exact
`new_view('1TCD')` workflow. Explicit clear restores Welcome; failed initial JSON
loading and a genuinely empty widget also restore/show it. The Python intent/reset
guard passes. The browser entry is registered in the required core lane and its
bounded guard profile is documented in the reporting protocol.

## Resolution

Resolved in source on 2026-10-20, with the guarded implementation above and the
runtime regenerated through `build:runtime`. The exact new-view PDB workflow
and bundled TcTIM each pass binary, JSON, failed-load and empty-view receiving.
The existing progressive/Studio/region/session/extraction guard and the
shape-only/panel/canvas-popup guard pass. JS units pass 330/330; TypeScript and
Ruff pass.

The single full Python core run returned 3,138 passed, 21 skipped, 12 experimental
Qt deselections and two failures: the deliberately pinned E2E inventory needed
47 after the new guard, and #248 exposed a stale provider-status README row.
The corrected inventory and addon-table modules plus initial-intent test pass
14/14. The full suite was not repeated or relabelled as green.
The [receiving receipt](../initial_welcome_validation_20261020.json) preserves
these scopes and subsequent hosted results separately. This is source receiving,
not an installed-candidate, standalone-GPU or new public-release qualification.
Human notebook receiving requires kernel restart and page refresh to replace
both Python classes and the page-global runtime cache.
