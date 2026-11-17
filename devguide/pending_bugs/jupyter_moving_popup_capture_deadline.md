---
summary: Diagnose a late moving-session capture from the actual Jupyter canvas popup.
issue: uibcdf/molsysviewer#344
status: active
opened: 2026-11-17
closed:
severity: medium
verification: measured
area: [jupyter, capture, popup, synchronization, performance]
guard: tests/test_jupyter_live_capture.py::test_live_jupyter_work_files
normative:
blocked_by: []
supersedes: []
---

# Moving popup capture deadline

Source `c08d4990` introduced the two guarded corrections below. The
complete actual-Jupyter work-file guard passes in `1018`, and Movie passes
separately. The later [full Linux source recovery](https://github.com/uibcdf/molsysviewer/actions/runs/44118070148)
on `0ea58be0` passes Python, all 25 notebooks and eight core entries, including
the separately corrected scientific mirror under
[#402](mirror_picking_fixture_camera_clipping.md). It then fails a moving-capture
test precondition, described below. Actual-Jupyter diagnostics are not selected
by that full-source profile. This report retains the intermittent popup
initialization failures. See [Validation after resumption](#validation-after-resumption)
for the current local results and covering source run.

Initial receiving `1004`, based on MolSysViewer `f2d83103` plus the peer-camera
correction and focused DataCard receiving, passes the complete native mirror
and DataCard entries. Actual-Jupyter Movie passes separately. The full
work-file case fails its eighth moving capture: Studio saves a session from
the canvas popup. Six stopped roundtrips, four Studio controls and the first
seven moving cases pass; this is not a complete work-file pass.

The requesting popup releases its two real held dynamic queries after its
second post-request frame change, at 1.235 seconds. A successful native
snapshot is sent 9.907 seconds after browser receipt of the request; Python's
cancel/timeout verdict follows approximately 47 milliseconds later. This
establishes late end-to-end delivery at the unchanged ten-second Studio
deadline, not a hung kernel or a demonstrated new MolSysMT defect. The popup
has native draws several seconds apart. The original traceback, actual
protocol timestamps, scientific readiness and native snapshots remain private.
The precise split among queueing, native drawing and transport is pending.

The prior [primary-presentation correction](../archive/jupyter_moving_capture_current_projection_timeout.md)
and its passing full receiving remain evidence for those exact earlier
inputs. This new negative neither proves a recurrence of that primary race
nor invalidates #400's independently received idle-camera correction. The
shared historical issue is reopened for this actual moving-capture boundary.

The complete `1004` invocation exits 1 in 834.20 seconds with 9,997 fixed
inputs, no resource stop, zero cgroup OOM events and all 68 owned processes
retired. The family has a 4-CPU / 4-GiB cgroup with no swap; summed process
RSS is not exclusive physical memory. Actual isolated ipykernel 7.4.0,
MolSysMT `4b0b1f8a`, Mol* 5.13.1 and explicit Node 22.23.4 are source
receiving, not an installed, native-GPU, Qt or human acceptance claim.

Next receive bounded passive popup queue/draw/transport timings before
choosing a correction. Keep both healthy five-second defaults, all six
explicitly delayed ten-second cases, actual two-frame/query controls, native
file equivalence, independent restore, cancellation, expiry and source
preservation. Do not increase the product deadline, repair-seek, suppress
scientific dependencies or combine seven passing cases with a different
invocation to declare the full guard passed.

## Passive popup timing — 2026-11-17

Instrumented `1008` retains the original full owner, all scientific assertions
and five-/ten-second deadlines on committed source `4f2d8fa2`. It again
passes seven moving cases and fails the final Studio-popup session. Its
browser observes cancellation 10.384 seconds after request receipt; the
successful native reply is sent another five milliseconds later. Native
draw observations retain a visible, focused popup. This is a reproduced
current boundary with diagnostic overhead, not canonical qualification.

The session CPU-sampling interval spans 33.766 seconds around form setup,
kernel status and capture. Its sample attribution contains 8.196 seconds in
native `bufferSubData`/`bufferData` bridge calls. This can include waiting;
it is not a GPU timer, buffer-size measurement or proof of a particular
geometry owner. Native draws are several seconds apart. One queued
`interaction_frame_complete` spans 7.340 seconds, including the awaited
presentation fence; do not treat that as exclusive JavaScript execution.
The profile also records repeated catalogue/Studio DOM construction.

All 9,997 selected inputs remain fixed, no resource/OOM stop occurs and all
19 owned processes retire under the same 4-CPU / 4-GiB envelope. The raw
CPU profiles, delegated timing observations and original failure are privately
preserved. Next attribute the slow buffer operations to actual native
objects/byte ranges and compare their updates with the scene's real changes.
Receive any correction against the original complete uninstrumented owner;
do not reduce render quality, pause another view or extend the deadline.

## Native buffer attribution and implicit cell

Diagnostic `1010` fails setup on an escaped diagnostic string before loading
the widget; its original is retained. Corrected `1011` delegates actual buffer
calls and associates array identities with native representation attributes.
Its browser passes all eight moving cases, cancellation, expiry and independent
recovery. The added raw trace exceeds the ordinary safe-summary size limit;
that summary remains unavailable rather than relaxing the limit. This is an
instrumented browser positive, not the canonical pytest qualification or proof
that the intermittent timeout disappeared.

The slow native calls include Distance lines (`aStart`, 207,936 bytes) and
the hidden Unit Cell mesh's index buffer (97,920 bytes). Their longest observed
calls take 3.232 and 3.018 seconds respectively. These are delegated-call wall
times, which can include queued graphics work. The deliberately displaced
atom in the original fixture is 100 nm farther along each axis in one frame;
its long dashed distance retains sizeable native arrays in later frames.
Buffer ownership and changing versions alone do not prove unchanged bytes.

The installed Mol* 5.13.1 default hierarchy preset creates a hidden unit-cell
representation unless `showUnitcell: false` is explicit. MolSysViewer already
owns its separate twelve-edge box. Regression `1012` confirms that the old
loader allocates one hidden native render object beside it. All four loader
routes now use the existing native opt-out; molecular cell data, the managed
box, image quality and deadlines are unchanged. No Mol* source is patched.

Receiving `1013` passes all 495 JS cases, types, normal builds and the complete
native box entry, including the new absence assertion and existing static,
widget/popup, navigation, explicit-cell, replacement, editing, hide and clear
controls. The original failure guards this actual native allocation. This
delivers one concrete reduction of unnecessary work; the original complete
uninstrumented Jupyter guard and relevant covering source checkpoint are still
required before closing the broader moving-capture report.

The auxiliary Mol* clone is clean `master` at
`dabbf29f952880a034a9637e28c9844e3ae73d9f`; its newer graphics package exposes
an object transform for transient placement that explicitly excludes CPU
instance readers. It is not a direct replacement for coherent callout loci,
picking and persistence. Ordinary builds continue to consume installed 5.13.1;
the existing native `showUnitcell` option solves this loader allocation without
adopting the development architecture.

## Capture preparation invalidates a valid prefix

Uninstrumented `1014`, with only the implicit-cell correction, still fails:
the second healthy/default Python capture times out at five seconds. The
current frame's native trajectory, box, shapes and annotations are ready, but
interaction and dynamic-region replies lag. The separate Movie case passes.
Removing the hidden cell is an independently guarded reduction of work, not
a complete explanation or repair of the capture timeout.

Native regression `1015` then observes a concrete preparation defect on the
real stopped, evaluated-empty frame. Before preparation there are zero dynamic
requests and the scene is coherent. Calling `prepareMovingVisualCapture`
creates one new request and makes the same frame unready. The new evaluation
is unnecessary: the applicable membership was already applied. In playback
that self-invalidation reopens frame advancement and can starve the requested
coherent draw. This identifies a race class; it does not reconstruct every
earlier event order or attribute scientific-provider failure.

Preparation now preserves the current applied membership only when no dynamic
query is pending or in flight. Missing/pending science follows the existing
path. Molecular and region edits retain their stamp invalidation, and capture
still requires a fresh native draw and the frozen-recipe checks. `1016` passes
495 JS cases, types/builds and the complete native lifecycle entry, including
the new preparation assertion on primary and popup plus original hidden,
detached, closed-owner, transport-loss and static-freeze controls. This run
uses 8 CPU / 4 GiB after the 4-CPU negative's near-240-second aggregate; its
existing operation and suite deadlines remain unchanged. The different
resource scopes remain explicit.

## Current uninstrumented receiving and remaining bootstrap observation

`1017`, with both runtime corrections at 4 CPU / 4 GiB, passes all six primary
moving cases, including both five-second defaults. It then fails the unchanged
30-second popup opening wait: `#molsysviewer-loading` remains visible. No
popup capture has been attempted. Its exact popup state was not retained before
cleanup, so neither a failed retry card, a stalled loader nor the original
#336 snapshot-expiry mechanism is established. The separate Movie case passes.

The maintained receiver now preserves bounded loader/controller/native state
before losing a failed `openCanvas` return, and rethrows the original error.
It introduces no retry or changed readiness predicate. On that receiver,
`1018` passes the complete ordinary pytest work-file guard in 309.45 seconds
under the same 4-CPU / 4-GiB envelope: six stopped roundtrips/strong restores,
four Studio controls, all eight moving captures, independent file recovery,
source preservation and cancellation/expiry without late writes. The new
failure observer is not exercised by this positive. Actual Movie receiving
remains the separately passed case in `1017`, not another result in `1018`.

The [current receipt](../live_capture_preparation_receiving_20261117.json)
retains both causal regressions, all original attempts, exact scopes and
private custody. This delivers the preparation and hidden-geometry fixes.
The report remains open for the intermittent popup initialization observation
and covering source qualification; a later complete pass does not explain
the earlier bootstrap timeout. Installed, native Qt/GPU, human and final
candidate acceptance remain separate.

## Later source recovery and actual-host diagnostic

Run `44118070148` on exact MolSysViewer `0ea58be0` and MolSysMT
`4b0b1f8a` finishes failed. All 4,747 Python cases pass, with 42 skips and
17 deselections; all 25 notebooks and the first eight core entries pass,
including the complete scientific mirror. The ninth entry saves its first
moving state successfully, then fails `Python must actually hold the dependent
request`. It does not time out. The test arms a hold and immediately saves,
assuming capture preparation will create a new query. That assumption no
longer holds for a current, already evaluated frame after the guarded prefix
correction. Restoring that unnecessary production query would reintroduce
the reproduced defect.

The revised adversarial setup waits for a real subsequent-frame scientific
request to be held before requesting Save. Its focused native primary control
`1033` passes in 32.15 seconds: the source save remains pending until release,
two actual post-request frame changes occur, the native scene agrees with the
file and independent recovery, and the source is unchanged. This is one
focused control, not the complete core entry or covering CI. The stopped,
already coherent evaluated-empty control separately requires no new query.
All product and readiness deadlines remain unchanged.

Complete canonical core receiving `1035` subsequently passes type checking,
the normal E2E build and the entire `moving-state-capture` entry, including
all six moving primary/popup/detached state/session saves, the stopped-empty
save and both annotation-presentation projections with native text, leaders,
CPU loci, alternate-camera PNG, restoration and GPU selection markers. Its
original 300-second entry budget is unchanged; the outer type/build/runner
invocation takes 300.32 seconds. All 9,997 selected inputs remain fixed,
there is no resource stop, and all 25 owned processes retire under 4 CPU /
4 GiB. This validates the adversarial test correction locally, not the
actual-Jupyter mismatch or covering hosted recovery.

Actual-Jupyter diagnostic `1029` opens both ordinary and moving popups,
retaining the delegated native/bootstrap trace before cleanup. It passes
six stopped roundtrips, six strong restores, four Studio controls and six
primary moving captures. It fails later in the first popup capture because
the saved snapshot is absent from the test's retained native-draw observations.
This is not a repeated bootstrap timeout or a demonstrated provider defect.
The original `1017` initialization cause remains unknown. The next diagnostic
observes matching native draws at reply arrival, before asynchronous file
completion can evict bounded history. No render verdict or scientific value
is supplied by that observer.

Diagnostic `1034` reproduces the same first-popup comparison failure. At
the real reply seam, all six primary replies have a matching independent
native draw; the popup reply has none and its observer has retained zero
coherent draws. Later file completion therefore did not evict a matching
sample in this invocation. Popup readiness nevertheless contains completed
draws with all recorded dependency gates satisfied. Delegated native-read /
draw-order observation is next, including the previously omitted system-sync
gate. The cause is still unestablished; do not change product state or relax
the native comparison based on the disproved eviction hypothesis.

## The diagnostic observer rewrites its own embedded bootstrap

`1036` delegates native `didDraw` and `readMovingVisualState` without replacing
their results. The popup returns coherent state inside real completed draws,
including the production capture read, but the diagnostic inspector never
returns. This narrows the discrepancy to observer execution rather than
establishing missing native presentation.

The bounded first-popup startup probe `1037` retains the actual script error:
`Unexpected identifier 'widget'`. The popup's `Node.appendChild` observation
hook rewrites any script containing `await boot(module)`. The classic harness
bundle also contains that text inside its embedded popup template. Injecting
the expanded diagnostic prelude into that literal corrupts the harness; it
has no exported native inspector. Playwright's script insertion resolves
without rejecting that runtime syntax error, and the later RxJS observer
therefore never records a draw. This explains the apparent native mismatch in
`1029`, `1034` and `1036`; those instrumented negatives do not demonstrate a
product capture failure. Their original failures remain preserved.

Both maintained popup observation hooks now require the actual module script,
leaving the classic harness bytes untouched. With that one classification
change, the same startup probe `1038` loads the original inspector as a
function with no script errors. Both probes intentionally stop immediately
after observing this boundary and retain exit 1; they are a causal negative
and positive observation, not passed full-host guards. The maintained moving
receiver now checks inspector availability before installing draw observers.

The shared core helper also establishes a genuine held dependency before
owner-close and transport-loss captures, avoiding the same stale assumption
that preparation must requery a good frame. Complete latest native/lifetime
and ordinary actual-Jupyter receiving follow; `1035` precedes this final
helper/hook refinement. None of these changes modifies the production bundle,
scientific calculation, render quality or operation deadline. The original
`1017` bootstrap timeout remains unexplained and distinct from this identified
diagnostic fault.

## Current timeout receiving and repeated playback feedback

Ordinary pytest `1039`, with the corrected observation hook, passes all six
primary moving captures but reproduces the original 30-second opening timeout.
Its retained popup has 62 atoms, a synchronized system and active native state
updates. By the subsequent diagnostic read its loader is absent. There is no
retained bootstrap exception or demonstrated scientific-provider failure.
Passive `1040` observes the ordinary stopped popup becoming revealed and
removing its loader in about five seconds, but fails earlier than the moving
popup: the second healthy/default primary capture reaches its unchanged
five-second deadline. Scientific replies continue to arrive while that real
kernel execution is pending; this is not evidence of an unserviced-comm
deadlock. Neither invocation qualifies the complete guard.

The transport trace exposes a separate source of unnecessary work. The native
playback poll sends identical `trajectory_frame_changed` receipts every
200 ms while a frame remains unchanged. Python unconditionally regenerates
trajectory and measurement summaries for each receipt. Native causal control
`1041` completes its actual state capture, geometry assertions and independent
restore, then fails the new no-duplicate assertion with **23 identical
consecutive receipts**. No scientific values are fabricated by this control.

The working runtime now coalesces identical feedback messages; frame,
playing state, navigation revision and the resolved box projection all remain
part of the signature. Stopping playback resets the signature so a new
playback episode reports its initial state. This does not change frame pacing,
queries, coordinates, rendering quality or capture deadlines. It removes a
measured contributor; its effect on the complete timeout workflow still
requires receiving.

`1042` passes all 495 JS cases, type checking and the normal runtime/harness/E2E
builds. The resource monitor then interrupts the invocation before its native
regression completes: 62.86 MiB of global swap-out in five seconds, 18.31 GiB
available, no cgroup OOM and all 29 owned processes retired. Retain the
completed checks and the interrupted overall result separately. The native
regression and full latest actual-host/core receiving remain pending; quiet
preflight observations are required before resuming expensive work.

After a fresh quiet preflight, `1043` is again interrupted during fixture
startup by the global swap threshold. All 15 owned processes retire, with
fixed inputs and no OOM; no latest native positive is claimed. Two consecutive
resource stops defer further expensive receiving. The [sanitized follow-up
receipt](../moving_capture_followup_receiving_20261117.json) retains exact
working-source/runtime hashes, provider scope, original failed CI and every
attempt's outcome. Its 188 original files are sealed in the approved private
custody, with matching SHA-256 and owner-only access. The original counters,
pending qualification and publication pause remain unchanged.

Preparatory `1030` cannot reach the systemd user bus from the sandbox, and
`1031` uses an incorrect relative helper path; neither reaches the fixture.
`1032` is interrupted after 17.10 seconds by the resource monitor when a
five-second global interval records 86.01 MiB of swap-in. Its cgroup has no
OOM events and all 15 owned processes retire. It is interrupted evidence,
not a product failure or passing guard. The later `1033` runs only after a
fresh quiet resource observation, with no resource stop and all 15 owned
processes retired. Its 4-CPU / 4-GiB containment is not a reservation.

## Validation after resumption

`1044` stops on 27.03 MiB of global swap traffic in five seconds with
18.11 GiB available and no cgroup OOM. All 16 owned processes retire before
the fixture is ready. After a longer quiet preflight, the reduced 2-CPU /
3-GiB scope `1046` passes the native regression in 54.32 seconds.
It observes 35 receipts across all three frames, zero consecutive duplicates,
a genuinely pending scientific request, coherent capture and independent file
recovery. All 15 owned processes retire and all 9,997 selected inputs stay fixed.
The expanded unit case also passes in the complete 495-case JS bundle. It
checks same-frame changes to the box and navigation revision, a different
frame, and fresh feedback after playback stops.

Canonical actual-Jupyter pytest `1047` passes in 350.53 seconds under 4 CPU /
4 GiB. It receives all six stopped roundtrips and strong restores, four Studio
controls, eight moving captures and no late write after cancellation or
expiry. Both moving popup saves pass, along with the two default Python saves
and all six deliberate held-query saves. The runtime is `d4c479e9…`, with
MolSysMT frozen at `4b0b1f8a`. All 9,997 selected inputs remain fixed, peak
scope memory is 2.86 GiB, and all 20 owned processes retire without a resource
stop. This qualifies the current local workflow. The intermittent failures in
`1017`, `1039` and `1040` retain their original results and causal limits.

The canonical core runner `1048` passes the box and moving-state entries
under 4 CPU / 4 GiB. The latter includes all seven saves and both annotation
projections. The lifecycle entry receives hidden-canvas recovery, closing
both popup owners and genuine transport loss, then hits its unchanged
240-second suite limit during the second fixture's dynamic-freeze scenario.
The combined command therefore fails. All 38 owned processes retire without
a resource stop.

The same lifecycle entry passes in isolation in `1050` with 8 CPU / 4 GiB
in 173.43 seconds, including both fixtures and their cleanup. The 240-second
suite limit and every operation deadline stay fixed. All 18 owned processes
retire with unchanged inputs. The latest code passes the scoped local
browser checks across these explicit profiles. Offline checks pass 574 cases
and skip three opt-in host cases. The reviewed source is integrated in
`d8c10784`. The single [covering Linux source run](https://github.com/uibcdf/molsysviewer/actions/runs/44176403184)
on that exact commit is in progress.

## Popup startup timing on the reviewed source

The original `1039` wire trace receives the canonical snapshot 5.53 seconds
after its request. It shows that the molecular transfer and snapshot reached
the notebook. Since that attempt did not retain popup-local timing, the
subsequent delay cannot be assigned to a particular native operation.

Passive diagnostic `1051` on bundle `d4c479e9…` passes all eight moving
captures and the cancellation and expiry controls. The stopped popup is
ready 5.05 seconds after the driver's readiness wait begins. The moving
popup is ready at 20.80 seconds. Its snapshot arrives at 6.08 seconds, the
loader starts fading at 18.96 seconds and is removed at 19.91 seconds.
Before fading, the popup applies the snapshot's frame 2 and then the host's
current frame 0. Those two native operations take 5.92 and 5.43 seconds.
The first loader observation predates the driver's moving-popup wait by
8.57 seconds. These are stage timings, not click-to-ready latency.

Experimental `1052` delegates all native work except a hypothetical
superseded, plain snapshot frame. Its branch requires a different host frame,
the same navigation revision and active playback. Both projections in the
observed moving popup select frame 1, so the branch never runs. The first
native projection alone takes 10.06 seconds. The driver sees the popup ready
at 16.16 seconds and all eight moving captures pass. The difference between
these runs provides no evidence of a speedup from omitting a frame. Preserve
the current product code and the documented deadlines. Both diagnostics use
4 CPU / 4 GiB, preserve all 9,997 selected inputs and retire all 20 owned
processes per invocation without a resource stop. Their original timing
evidence is in the private supplement identified in the follow-up receipt.

## MolSysMT coordination checkpoint

On 2026-11-17 the MolSysMT owner reports main
`a57f4c51b4feafc54cad2677c862cae85c4e2534`: portable attribution metadata
under #292 and H5MSM recipe corrections under #772, with 1,933 source cases
and 42 public-Ackredit controls passing in its declared scope. The owner
reports unchanged detectors, codec and native binary `4ffb82e4…`, and requests
neither a new matrix nor publication. These are owner-reported results, not
MolSysViewer receiving or an installed pair. Keep the frozen `4b0b1f8a` input
for this investigation until explicit source adoption; the checkpoint does
not change #344's pending browser qualification or the final-pair identity.
