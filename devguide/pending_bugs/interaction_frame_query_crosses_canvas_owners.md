---
summary: Interaction frame query replies reach unrelated renderer-local request IDs.
issue: uibcdf/molsysviewer#337
status: active
opened: 2026-11-08
closed:
severity: medium
verification: reproduced
area: [interactions, popup, transport]
guard:
normative:
blocked_by: []
supersedes: []
---

# Interaction frame queries cross canvas owners

## What

Native moving capture under #319 shows primary and popup renderers reusing
their independent integer request IDs for different frames. For example,
request 29 appears for frame 1 at 63.578 s and frame 0 at 86.382 s. Python
broadcasts geometry and completion to all endpoints, while the local completion
handler accepts the matching integer. A foreign completion can therefore retire
a local pending query before its own answer arrives. Frame checks protect
application of different-frame links; they do not scope completion identity.

The real pentalanine/sparse-Interactions control in
`tests/test_interactions_scene.py` independently receives eight messages for
one query with two canvas endpoints and one detached panel, instead of two
requester-owned messages. Four controls fail before correction. Raw logs and
JUnit are retained under the private working receipt's `query-before-01`.

## How

`_handle_frontend_event_guarded` sends `set_interaction_frame` and
`interaction_frame_complete` without a destination; the normal scene delivery
path fans them out. The trusted frontend host did not retain the originating
canvas when forwarding a query. Panel-only controllers also requested graphical
geometry when the authority's summary frame differed from their unused local
frame.

The working correction stamps the owner at the authenticated widget/Qt host
boundary, validates an existing primary/canvas destination in Python, and
targets geometry, completion and failures only to it. Legacy primary requests
remain primary requests. Live Qt explicitly reports authenticated popup
open/close lifetime; its host relays targeted replies instead of applying them
to its own canvas. Closed, unknown and panel endpoints cannot request geometry.
Scene-wide interaction edits still follow the ordinary scene delivery path.
Panel-only summaries retain revision guards without requesting hidden geometry.

## Why

Each renderer owns its own current native frame and pending geometry. A query's
integer is not globally unique. Correct isolation is required even if capture
timing has additional causes.

## What was refuted

Increasing the resource ceiling alone did not stabilize the original receiving.
The eight-CPU/six-GiB attempt `endpoint-after-06` timed out without cgroup CPU
throttling or resource interruption. The follower no-op refinement subsequently
receives popup-state, but popup-session still times out in `endpoint-after-07`.
This report does not assert that query isolation alone explains every timeout.

## Remaining receiving

The source correction passes 54 affected Python cases, 485 transport/router/
Qt/reporting controls and 422 canonical JavaScript cases. Strict production
TypeScript, runtime, harness and E2E builds pass. One mistyped Python test path
produced an exit-4 usage error without running tests; the corrected selection
and both raw records are retained separately.

The unchanged native four-role attempt receives popup-state and popup-session,
including exact native geometry, source immutability and independent file
restoration. Detached Studio state still reaches `request_timeout`; its session
case does not execute. Inputs remain fixed (4,329), all thirteen owned processes
close, peak aggregate RSS is 3,119.5 MiB and minimum system-available RAM is
9.62 GiB. The one observed cgroup throttling interval totals only 168 µs;
there is no resource interruption. Qt's new host-routing path still needs
native host receiving; protocol tests do not replace that observation. The
canonical v1 popup bootstrap/late reply/Retry control passes on the final
backend bytes in 41.16 s, with fixed inputs and thirteen owned processes
closed. Its stopped-frame geometry oracle does not receive moving saves.

See the [timing receipt](../moving_capture_popup_timing_receiving_20261108.json).
The bounded issue remains open while integration receiving continues. These
results do not complete A5, qualify all endpoints or advertise visual-state
capture version 2. Movie #320 remains mandatory under #315.
