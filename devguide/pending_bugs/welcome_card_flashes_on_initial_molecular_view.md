---
summary: Welcome card flashes before the initial molecular view is rendered
issue: uibcdf/molsysviewer#247
status: open
opened: 2026-10-20
closed:
severity: low
verification: asserted
area: [loading, ui, lifecycle]
guard:
normative:
blocked_by: []
supersedes: []
---

# Welcome card flashes before the initial molecular view is rendered

**Reported:** 2026-10-20, first observation in Diego and Liliana's pre-1.0
TcTIM / PDB 1TCD exploratory dogfooding. The transient is a human observation
on the notebook canvas before successful molecular rendering. Source inspection
is recorded below; no automated initial-load reproduction has been performed.

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

In `molsysviewer/js/src/managers/viewer-controller.ts`, the controller constructor
calls `updateWelcomeState(true)`. The initial `structureLoadPending` value is
false. The `hasInitialStructures` option suppresses Welcome only when the caller
sets `isInitPhase`; ordinary updates can still use the empty-state branch.
`molsysviewer/js/src/index.ts` reads the widget's `initial_messages` before
controller creation and replays those messages afterward.

This exposes an inspection lead around initial controller setup, state updates
and replay before a loader establishes its pending state. The complete causal
call sequence and the reporter's exact loaded frontend bytes remain unverified.
Do not describe the lead as an automated browser reproduction or a proven cause.

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
required absence of the transient. No runtime fix is included in this report.
