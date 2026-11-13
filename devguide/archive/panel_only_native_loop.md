---
summary: Stop unused native rendering in panel-only Studio windows.
issue: uibcdf/molsysviewer#379
status: resolved
opened: 2026-11-13
closed: 2026-11-13
severity: medium
verification: inspected
area: [studio, rendering, lifecycle]
guard: molsysviewer/js/tests/e2e/panel-popup-welcome.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Resolved: unused panel-only native animation loop

Resolved in source and actual-browser receiving: panel-only initialization
stops its native animation loop with `noDraw`, retaining real parameter/UI
state and the active associated molecular canvas.

`MolSysViewerController.create` initializes Mol*'s viewer and starts its native
animation loop for every controller. A panel-only controller then hides its
canvas and receives UI/metadata projections. DOM visibility does not stop that
loop. Keep the real plugin/renderer parameter state and origin-canvas routing,
but stop unused native rendering for this endpoint type. Ordinary canvases,
their trajectory and scientific calculations must remain active.

This is a bounded resource correction under #372, related to #378's incomplete
detached-panel receiving. Diagnostic `722` receives the selected real panel
closure/transport controls with earlier cases explicitly ablated. Its CPU
sample observes native WebGL initialization/disposal cost in the shared
isolate; it does not isolate the unused loop's cost or prove it is the sole
cause of the earlier bootstrap failures. The broad texture-argument filter
also includes non-sized `texImage2D` overloads: its aggregate is not a qualified
atlas-upload count. Original data remains private and unchanged.

Receive stopped panel-only/native and active molecular loops in the actual
browser, preserving hierarchy/addon controls and the nested Studio work-file
and cancellation routes. Do not substitute a fake renderer, reduce quality or
count diagnostic ablation as canonical full receiving. A complete renderer-free
UI architecture is outside this correction. The reviewed inventory has four
pages/349 issues before this report.

## Resolution

The bounded correction passes native project types, runtime/harness/entry
builds and all 475 units in `723`. Canonical `724` receives stopped panel and
active molecular loops, real hierarchy and addon protocol, shape-only
Render/Clear, remount, both popup modes and later molecular loading.

Canonical persistent Studio `729` additionally receives state/session
save/restore and camera intents from primary, canvas popup and nested detached
Studio, with exact originating camera/frame and genuine pending cancellation.
It asserts the stopped panel and active associated native loops. Native exit
is 0 in 350 seconds, inputs are unchanged, peak summed owned RSS is 2,923.2 MiB,
and there is no resource stop, cleanup error or surviving owned process.

The first new assertion in `726` used an uninstrumented nested controller
handle. Its failed entry remains preserved; observing the actual nested
`window.open` controller creation fixes the test without substituting product
state or replies. Registration/build controls pass in `727`. No diagnostic
ablation is counted as canonical acceptance. Full-core, actual-host, installed
and human gates remain under #372. The independently reproduced panel PNG
routing defect is tracked separately in #380.
