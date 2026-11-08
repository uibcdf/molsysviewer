---
summary: Canvas popup discards its canonical scene when molecular loading outlasts the snapshot wait.
issue: uibcdf/molsysviewer#336
status: resolved
opened: 2026-11-07
closed: 2026-11-08
severity: medium
verification: reproduced
area: [popup, transport, restoration]
guard: molsysviewer/js/tests/e2e/popup-scene-bootstrap.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Canonical popup scene expiry during molecular loading

**Delivered in `11402e9b`, independently verified on origin/main; #336 closed.** This is a bounded child
of #319/A5, not another original-plan completion. The frontend advertises only
capture version 1. All publications remain paused.

The extended moving guard uses the real widget/Python authority and actual
Studio work-file controls. Diagnostic attempts `endpoint-after-01` and `-02`
return positive captures but fail the actual popup sphere geometry assertion;
annotations and distance geometry are absent too. Their primary canvas has
those objects. Attempt `-03` times out saving and preserves the bootstrap order:
the actual popup applies its typed molecular payload at local times
5.977–10.299 s, receives an initial sync with an empty messages array at
10.304 s, and never receives the source's complete 32-operation scene snapshot.
The widget receives that real snapshot later, but its five-second request
expiry has deleted the correlation. No fake scene or capture verdict supplies
this observation. The final attempt retains 4,323 unchanged inputs and closes
all thirteen owned processes in 59.20 s, without resource interruption.

Python correctly defers the snapshot until this endpoint reports its molecular
generation applied. The host's reply deadline nevertheless includes that load,
then treats expiration as an empty successful bootstrap. Its stream-complete
handler also releases queued live projections before the canonical scene.
This differs from #238's stopped-frame convergence and #300's addon catalogue.
The complete issue inventory was inspected: pages 100/100/100/34.

The correction must retain a correlated request through the independently
bounded molecular progress, with a separate response deadline after completion.
Cancel it on endpoint close, replacement and widget disposal. Keep the bootstrap
barrier until the actual canonical snapshot is delivered; failure must remain
visible and recoverable rather than silently producing an empty canvas.
Late/foreign replies and stale generations must not revive another request.
The five-second silent-response limit, thirty-second molecular progress limit
and actual capture operation deadlines remain bounded; no generic timeout
increase substitutes for the causal correction.

The new private diagnostic records are under
`.pytest_cache/robustness-20261106/A5-moving-endpoints-20261107`; the public
[endpoint receipt](../moving_capture_endpoints_receiving_20261107.json) records
their scope. Attempt 01 did not preserve its original saved JSON beyond the
cleaned fixture workspace. Attempt 02 does preserve that original file after
moving its copy ahead of the failing geometry assertion. Attempt 03 saves no
successful artifact. Original failures remain intact. The first extra observer
rolled away its earliest bootstrap entries; the third attempt explicitly
preserves the first 128 and the last 24 observations.

An automatic approval rejection due to occupied swap prevented one command
from starting. Seven fresh read-only samples over twelve seconds showed
15.77–15.79 GiB available, zero swap traffic and zero memory PSI. Subsequent
approved runs used four CPU, a 4-GiB cgroup, no swap and a resource monitor;
all owned processes closed. No other user's processes or swap were changed.

## Resolution and scope — 2026-11-08

The request owner now retains correlation through the exact endpoint's
flow-controlled molecular generation. Source silence still expires at five
seconds; accepted molecular progress has its existing thirty-second bound and
completion starts a fresh response wait. Foreign destinations and stale
generations cannot extend it. Endpoint close, replacement and widget disposal
retire owned requests/timers. The host keeps queued live projections behind
the canonical snapshot and discards them on bootstrap failure.

The popup keeps its loading surface until the actual scene has been applied.
Failure shows a recoverable message and an actual **Try again** button instead
of an empty successful bootstrap. Expired replies cannot revive it. Captures
before a completed bootstrap reject as `NoLiveCanvas`. No public Python API,
scientific calculation, second playback clock or capture deadline is added.

Production TypeScript, runtime build and ten directed request-owner cases pass.
The canonical JavaScript index passes 416/416 without omissions. Its popup UI
and host tests also receive failure/retry and real bootstrap-before-capture
ordering. The separate canonical native guard
`popup-scene-bootstrap.e2e.ts` passes in 51.75 s with 4,327 unchanged inputs
and all thirteen owned processes closed (peak 2,525.3 MiB). It withholds an
actual Python scene reply at the comm seam, receives visible failure, delivers
the original late reply, clicks Retry and receives the real complete snapshot.
It runs playback during bootstrap and deliberately stops at frame 1 for the
geometry oracle: sphere `[10, 0, 0]` Å, cell basis `[0, 40, 0]` Å, anchored
annotation, actual distance endpoints and empty dynamic region. The molecular
object/coordinates stay unchanged and the follower owns no playback timer.
It uses shipped version-1 capabilities, not negotiated moving capture.

The preceding corrected-source moving attempt `endpoint-after-04` applies the
full 32-operation scene and creates sphere, labels and distance, then still
times out saving during uninterrupted playback. That failure remains owned
by #319; it does not reopen this separate bootstrap cause or qualify A5.
Full moving popup/detached saves, hidden endpoints, actual Jupyter and
consolidated/hosted acceptance remain. No deadline or scene assertion was
relaxed to close this bounded defect. The original count stays 8/46 delivered,
1/46 finally accepted, with Movie #320 mandatory and publication paused.
