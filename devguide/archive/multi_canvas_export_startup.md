---
summary: Independent exported HTML starts slowly while other molecular canvases draw.
issue: uibcdf/molsysviewer#400
status: resolved
opened: 2026-11-16
closed: 2026-11-17
severity: medium
verification: measured
area: [export, rendering, performance]
guard: molsysviewer/js/tests/e2e/trajectory-plot.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Independent HTML initialization with other live canvases

**Resolved in source:** peer-camera identity excludes Mol*'s endpoint-local
scene bound, eliminating repeated unchanged-viewpoint resets. Full native
snapshots and authority/draw semantics remain intact. The complete canonical
plot entry and bidirectional scientific mirror pass; the separate current
moving-session deadline under #344 remains open.

**Pre-1.0 under #315.** The numerical plot correction belongs to #321;
this report owns the separate initialization boundary reached before its
precision controls. Closed #391 corrected streamed reply ownership and
hidden-iframe polling; no recurrence of that mechanism is established.

Local canonical `959` and source run `43796373853` miss the unchanged
30-second exported-controller guard; first-controller observations arrive
at 37.23 and 42.392 seconds. The document is visible, a canvas exists and
there is no recorded page/request error. Current input is declared Mol*
5.13.1 and real Chrome/SwiftShader, with three other live molecular canvases.
The [receipt](../residual_four_issues_receiving_20261116.json) identifies each
Node version, native input, resource limit and distinct receiving scope.

Private Node-22 diagnostic `966`, at 4 CPU / 4 GiB, retains a native CPU
profile: state/extension/context initialization dominates, including 11.22 s
in `createState`. Bare unmodified Mol* control `969` initializes in 0.470 s,
but has different context attributes and no other live canvases. Do not
infer an upstream defect or universally slow initialization from either.

Diagnostic `972` stops the other three actual native draw loops during
initialization, then restarts them. With the same Node, resource ceiling
and profiler, the static profile takes 6.551 s and the complete plot entry
passes in 150.30 s, including all fifteen Decimal controls and independent
HTML/hidden-iframe coordinates. This discriminates draw-loop interference;
the scheduling intervention is not an accepted production fix or canonical
qualification. Original failures and setup-only errors remain preserved.

Investigate native scheduling and choose a bounded solution that preserves
the other views' ordinary interaction and animations. Do not silently stop
another view, prewarm the guard, change rendering quality, weaken numerical
or molecular assertions, or increase initialization's bound just to pass.
Receive the unchanged complete trajectory-plot entry, retaining physical
coordinates, authority, independent exports, popup behavior and raw values.

Duplicate review uses four complete pages, 371 issue/PR records and 345 issues,
including closed records. #47 is deferred editorial export review, #391 has
a different resolved mechanism, and #399 owns receiving preparation.
No release, native-GPU throughput or installed qualification is claimed.

## Passive peer observation — 2026-11-16

Diagnostic `991`, on source `303c9152` with the same runtime as `b8461576`,
delegates existing native ticks and GL methods while counting their calls;
it adds no tick, stop/restart, delay, changed input or quality setting. The
30-second guard again fails; the first controller is observed at 32.308 s.
All 9,998 selected inputs remain unchanged, the 4-CPU/4-GiB scope has no
resource stop and all 18 owned processes retire. This is an instrumented
negative diagnostic, not canonical qualification or a product correction.

During the approximately 32.8-second observation, the three peers receive
31/34/54 native ticks and report stopped trajectory playback throughout.
The toy page completes no new draw; the live source and its popup complete
34/54 draws. Raw draw counters are 1/35/55 because Mol*'s `didDraw`
BehaviorSubject replays its existing value once when subscribed. The
source/popup continue rendering while nominally
stopped; that alone neither identifies their trigger nor proves that all
draws are unnecessary.

Delegated JavaScript time in dimension reads is below one millisecond per
peer; asynchronous GPU work is not measured by those method timings. Do not
introduce a dimension cache, idle throttle or global pause on this evidence.
Next discriminate real draw requests, camera transitions and accepted peer
messages before choosing a fix. Preserve the original numerical/scientific
entry and its deadline. The [consolidated receipt](../residual_four_issues_receiving_20261116.json)
owns the exact counters, manifests and private custody.

## Resolution — 2026-11-17

Delegated diagnostic `994` observes 31 incoming camera snapshots and native
resets per source/popup, despite unchanged viewpoints and stopped playback.
Only `radiusMax` differs: 18.00454099 versus 18.07642711. The installed Mol*
5.13.1 `Canvas3D.resolveCameraReset` derives that value again from its local
scene. Treating it as a peer viewpoint change makes the two endpoints echo
forever. This is Viewer's relay identity defect, not an upstream claim.
That private observer also reads an unavailable native controls field;
its original errors are retained and it is not clean canonical receiving.

The production fingerprint excludes only that local bound. Every other
snapshot field and new authority revision still participates; full native
snapshots are unmodified for capture and persistence. A native-Camera unit
control guards those distinctions and nonmutation. All 495 JS cases, normal
types and builds pass in `996`. Corrected passive observer `999` receives
zero relayed resets while the two local bounds still differ. Its static
controller observation takes 4.806 seconds; it also passes every original
plot assertion. Observer/setup failures `993`/`997` remain separate.

Uninstrumented canonical `998` passes the complete trajectory-plot entry in
132.87 seconds with the original 30-second startup deadline, all fifteen
Decimal controls, raw values, authority callbacks, molecular coordinates,
popup and independent HTML/hidden iframe. Complete native mirror receiving
in `1004` additionally passes rotation, zoom, Focus All and Reset View in
both directions, single motion/playback clocks, native picks, scene geometry
and frame-specific interactions. No other canvas is paused or throttled.

The [current receipt](../camera_peer_and_ipc_receiving_20261117.json) preserves
exact inputs, original negative diagnostics and private custody. This closes
the identified source relay defect; covering CI, actual moving Jupyter,
installed, native-host and final-candidate acceptance retain their own scope.
