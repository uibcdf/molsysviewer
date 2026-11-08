---
summary: Camera-relative callouts use the previous camera basis on a completed draw.
issue: uibcdf/molsysviewer#330
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: measured
area: [annotations, camera, rendering, capture]
guard: molsysviewer/js/tests/e2e/moving-state-capture.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Camera-relative callout presentation

**Resolved:** bounded correction received; see the final section and shared receipt.


The unadvertised A5/protocol-2 receiver prototype based on `5390fadb` releases
its scene prefix so real Python frame-dependent replies can run. Its first
native pentalanine pilot nevertheless times out: all 39 observed draws fail
annotation coherence while the model traverses 29 applied frame entries and
actual dynamic-region replies continue. Four actual representation samples
have camera-basis position errors of 0.00149–0.00230 angstrom. All 4,314 inputs
stay fixed and thirteen owned processes close. Earlier attempts and the full
source `request_timeout` traceback remain in the private working evidence.

The existing controller invokes `annotations.onCamera` from `didDraw`; the
handler then starts an asynchronous representation rebuild. This is the
wrong phase for geometry that must describe that draw's moving camera. The
prototype observation is not a fresh rerun of the unchanged published artifact.
Its annotation success-path order is inherited from the inspected baseline.
The production frontend still advertises capture protocol 1 only.

Four full issue pages contain 328 issue/PR entries and 300 issues, including
closed ones. #146 covers anchor/offset APIs and persistence, #241/#243 cover
pickability/registry lifetimes, and open #325 retains a separate hosted GPU-pick
failure with no identified cause. This new mechanism has its own report and
does not increase the original 46-leaf audit denominator.

## Direction and required receiving

Keep semantic annotation specifications and frame-dependent anchor work
separate from synchronous camera presentation. Resolve the camera basis in
the render phase that actually consumes it, using the installed Molstar 5.4.1
APIs. Do not fix this by pausing/rewinding, introducing another clock, selecting
a hidden renderer or relaxing the capture comparison.

The proposed adapter must cover ordinary drawing, picking and image rendering;
retain all three offset components, world/absolute anchors, leader geometry,
CPU loci bounds/focus, native markers and edit/hide/clear/disposal. A render-only
matrix fix that leaves `Shape.transforms`/loci stale is insufficient. Camera
presentation must not queue asynchronous Mol* state transactions per draw.

Receive the original uninterrupted camera/trajectory case and state/session
restoration with real box, annotation, distance, sphere, hbonds and dynamic
region geometry. Keep primary/popup/detached and hidden-endpoint qualification
explicit. Movie #320 remains mandatory and needs its own timeline/visibility
capture contract; the prototype refuses an unqualified active Movie scene.

## First corrected native receiving

The working correction uses the bundle-local `Renderer.update` presentation
boundary, shared by drawing, picking and images. Camera-only motion updates
the native shape instance transforms and CPU loci together; frame-dependent
anchor rebuilding remains asynchronous. Weak context ownership releases only
the disposing view, and image completion restores the live presentation.
No new timing owner, forced pause/seek or per-camera state transaction exists.

The unchanged moving guard now passes in 70.44 seconds: real primary
`save_state_async` and `save_session_async`, with a matching completed-draw
scene, independent restoration, unchanged MolSys identity/coordinates and
playback still active. Both accepted samples happen to be frame 0 travelling
backward in ping-pong mode; this is not yet receiving of an empty selected
frame or all endpoint/offset/projection combinations. All 4,316 selected
inputs stay fixed and all thirteen owned processes close. The three original
failed attempts and full source traceback remain preserved.

Three presentation-owner, four playback-handler and eight annotation-handler
unit cases pass; the preceding fourteen request/filter/cancellation cases also
pass. These are overlapping directed selections, not a final canonical gate.
Still receive three-component offsets, CPU bounds and native GPU markers,
offscreen alternate-camera restoration, popup/detached/hidden behavior and
the applicable regression before closing this report or enabling negotiation.

The current working tree includes the receiver/readiness and resolved playback
metadata prototype plus these tests. These changes are not delivered
or advertised as a completed capability. A5 remains partial, with 8/46 delivered
and 1/46 finally accepted; candidate/tag/package and both 1.0 publications stay
paused.

## Expanded receiving in progress

The separate `moving-state-capture.e2e.ts` entry now belongs to the ordinary
core build/runner and has an addressable local reporting profile. It retains
the unadvertised negotiation and all uninterrupted state/session assertions.
The fixture now has three nonzero camera offsets `(6, 8, 5)`, a solid leader,
world/absolute controls and a separate explicit stopped-trajectory empty-frame
control. An alternate-camera PNG/native GPU-selection scenario follows them.

Canonical Node passes 400/400, TypeScript checks pass, the reporting suite
passes 381/381 and the changed Python files pass Ruff lint. These do not yet
qualify the complete expanded native entry. Its first failure compared
`Shape.Loci` raw geometry bounds with transformed positions; inspection of
Molstar's native contract showed that the correct transformed CPU object is
the group/instance loci. The helper now resolves those through the native
representation mapping without changing the world-position oracle or its
tolerance. The failed receipt remains preserved.

The next native run receives moving state at frame 0/backward and session at
frame 2/forward, including transformed text and group-loci centers, then times
out waiting for the explicit empty-frame navigation. It exits 1 after 50.41
seconds, with all 4,318 selected inputs unchanged and thirteen owned processes
closed. Its new PNG/pick phase was not reached. A diagnostic run is receiving
the actual authority/renderer messages before any causal conclusion or fix.

The isolated presentation phase subsequently passes in 50.72 seconds, with
all 4,319 inputs fixed and thirteen owned processes closed. It receives
perspective and orthographic cameras; all three nonzero offsets; actual native
text centers and solid leader endpoints; CPU group-loci and GPU instance
transforms; real alternate-camera 320x240 PNGs; immediate live-camera
restoration; actual GPU picks and selected markers. Both original PNGs were
visually inspected and retained. Execution used one systemd scope capped at
two CPU and 4 GiB with no swap; sampled peak owned RSS was 2,039.5 MiB. This
is the presentation phase, not a passing complete moving-capture entry.

[#331](late_playback_feedback_overwrites_python_seek.md) identifies the
empty-frame navigation failure. Its working correction then reaches and
captures frame 1, exposing [#332](dynamic_region_restore_uses_wrong_structure.md):
independent recovery materializes the dynamic region at the wrong structure.
Those separate prerequisites and the earlier intermittent moving-session
timeout remain visible before complete canonical and endpoint qualification.

The later complete entry does not pass. Its 420-second outer termination
stacks in the fixture's global transport drain: continuous playback can keep
adding traffic, so global quiescence is the wrong acknowledgment for a single
test command. The test adapter now returns that envelope's existing queue
promise and the moving scenario awaits it, leaving scientific assertions,
2-fps motion and the 12-second public save deadline unchanged. Original
termination evidence is retained, including `outer_timeout=true`; the child's
native exit 0 during cleanup is not a passing result. A recorded interpretation
of sustained GPU-process CPU as compilation was unverified and has a separate
correction note; the live scope was safely capped at four CPU after a measured
resource review, with the same 4-GiB/no-swap limits.

The corrected transport then reaches the public save acknowledgment, but the
full entry still fails with a source request timeout in 63.39 seconds. There
are nineteen applied frame entries and zero fully coherent sampled draws;
pending interaction/dynamic geometry is observed, while measured annotation
positions agree with the independent camera basis. All 4,319 selected inputs
remain fixed and all thirteen owned processes close; sampled aggregate RSS
peaks at 2,144.6 MiB under the two-CPU/4-GiB scope. This is not closure and does
not prove that all earlier timeouts had one cause. Next receive bounded
dispatch/release timestamps and individual applied readiness before changing
any scheduler, deadline, assertion or capability advertisement.

The complete expanded canonical native entry subsequently passes in 36.20
seconds after the independent #331–#333 corrections. It receives the moving
state/session and empty-frame controls, then both perspective/orthographic
image, CPU-loci and GPU-pick phases. All 4,319 selected inputs remain fixed;
thirteen owned processes close without survivors or cleanup errors. The
canonical Node selection now passes 404/404. Legacy Studio/controls receiving
and advertised-v2 endpoint qualification remain separate; this is working-tree
evidence and does not close A5.

## Resolved bounded correction — 2026-11-07

The canonical shared-browser selection passes all three complete Studio,
box-trajectory and moving-state entries in 429.86 seconds. It retains every
operation deadline and the 360/180/180-second entry budgets, with no skips or
pressure interruption. All 4,323 selected inputs stay fixed; thirty owned
processes close with no survivors or cleanup errors. Execution uses four
logical CPUs/400%, 4 GiB and no swap; sampled aggregate owned RSS peaks at
3,337.8 MiB. Source coordinates and all independent scene-geometry assertions
are retained. Canonical Node passes 406/406. The overlapping Python boundary
passes 672/672 on its recorded pre-final-camera source; its Python production
inputs remain unchanged by the later camera/test-only corrections.

See [the receiving record](../moving_capture_renderer_receiving_20261107.json)
for exact earlier scopes, original failures, the secondary diagnostic error
and the check-log reuse incident. Earlier controls receiving keeps its
pre-final-envelope/camera source scope; the final Studio guard receives those
changed camera/popup boundaries. This closes the bounded defect, not parent
A5/#319, hidden/protocol-2 endpoint or actual-Jupyter acceptance. The frontend
still advertises protocol 1 only. Original-plan progress remains 8/46 delivered
and 1/46 finally accepted; Movie #320 and all publication pauses remain.
