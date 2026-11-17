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

Current receiving `1004`, based on MolSysViewer `f2d83103` plus the peer-camera
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
