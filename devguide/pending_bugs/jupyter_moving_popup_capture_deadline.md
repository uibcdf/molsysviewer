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

Current source `c08d4990` contains the two guarded corrections below. The
complete actual-Jupyter work-file guard passes in `1018`, and Movie passes
separately. The single [full Linux source recovery](https://github.com/uibcdf/molsysviewer/actions/runs/44031725024)
fails at the scientific mirror's clipped sphere fixture, tracked separately in
[#402](mirror_picking_fixture_camera_clipping.md). Actual-Jupyter diagnostics
are not selected by that full-source profile. This report remains open for the intermittent
popup initialization failure in `1017`, whose cause is not established.

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
