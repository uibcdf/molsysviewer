---
summary: Exported HTML reports readiness before successful scene restoration.
issue: uibcdf/molsysviewer#129
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: high
verification: reproduced
area: [export, rendering]
guard: tests/test_exported_page_opens_from_disk.py::test_failed_scene_restoration_never_declares_the_export_rendered
normative:
blocked_by: []
supersedes: []
---

# Exported HTML declares success after failed restoration

**Reported:** 2026-10-01, real Chrome inspection of an exported pentalanine scene.

## What

Appending an interaction projection with an invalid radius unit to a real
snapshot logs `Interaction radius requires explicit nm units`, but the page
still reports `data-molsysviewer-rendered="true"` and displays a partial scene.

## How

`bootDocsView` starts initial-message application in a detached async closure.
`handleMessage` catches handler failures. The HTML boot script declares success
after a two-second timeout irrespective of the restoration's outcome.

Await the whole initial replay, use strict handler error propagation for exported
pages, and wait for a new Mol* `didDraw` notification before boot resolves. The
observable is a BehaviorSubject: its immediate replay of an old draw does not
count as a new one. Preserve live widget diagnostics and remove the fixed-delay
success marker. Failed boot must expose an error and never set the success flag.

## Why

HTML recipients and screenshot consumers cannot distinguish a partial scene
from a restored one. Readiness must describe what the artifact actually did.

## What was refuted

An additional timeout cannot establish correctness. The inspected scene did
draw 62 atoms, while its later interaction operation failed. A nonempty molecule
alone is therefore also insufficient evidence of complete restoration.

## Resolution

`bootDocsView` awaits every initial operation using explicit strict error
propagation, then requests and awaits a new Mol* draw with a 30-second draw
deadline. The observable's immediate replay does not count. Boot failures
reject, dispose the controller and expose a visible error instead of the
rendered marker. The fixed two-second success delay is removed. Ordinary
live-widget handler diagnostics preserve their default behavior.

The pytest guard opens an actual invalid exported artifact offline in Chrome
and asserts a visible error with no success marker after the invalid final
interaction operation. The whole eight-test disk-opening file passes. The
browser artifact suite observes Mol* draw counts at the moment readiness is
declared and requires a new draw after the last restored operation. Removing
strict propagation, awaiting the replay, or awaiting the draw makes the
corresponding guard fail; exact source bytes and runtime are restored.

The previous command-line Chrome virtual-time harness intermittently finished
before an actual GPU draw after readiness became meaningful. It was replaced
with a wall-clock Playwright helper, offline, with actual WebGL2; unavailable
WebGL2 is an error. This is Chrome/SwiftShader evidence, not a standalone
real-window/GPU observation.

Validation: full Python 2,330 passed / 20 skipped, JS units 293/293,
TypeScript checking, runtime build, core browser 36/36 and both performance
harnesses pass. Final expanded artifact checks pass after all mutations.
