---
summary: Dynamic-region query replies cross renderer frames and omit unchanged memberships.
issue: uibcdf/molsysviewer#338
status: active
opened: 2026-11-08
closed:
severity: medium
verification: reproduced
area: [regions, trajectory, popup, transport]
guard:
normative:
blocked_by: []
supersedes: []
---

# Dynamic region queries cross renderer frames

**Current receiving — 2026-11-08:** the combined browser entry receives all
seven actual moving saves and independent restorations, including both popup
types and their native region memberships. The new lifecycle entry additionally
receives a real budget freeze at frame 0 while both canvases display frame 1:
both use the frozen membership with frame-1 coordinates. See the
[host/lifetime receipt](../moving_capture_host_lifetime_receiving_20261108.json).
Actual Qt/Jupyter continuous v2 and Qt scientific query routing remain pending;
the actual-host stopped-scene passes do not close this issue. Earlier failed
experiments below retain their original inputs and scope.

## What

Actual moving-save diagnostics under #319 show dynamic replies broadcast to
renderers that can be at different native frames. `set_dynamic_region_atoms`
applies entries without checking the local frame. Completion compares a frame
number rather than an individual query; a delayed answer can also be confused
with a later visit to that frame.

Python returns only changes relative to its shared last evaluated membership.
A second renderer querying the same frame still needs a complete answer,
including explicit empty memberships, independently of that shared cache.

Four real pentalanine/MolSysMT controls fail before correction in
`tests/test_moving_state_capture.py`: requester-owned complete membership and
rejection of closed, unknown and panel-only owners. The coordinate stress case
and genuine selection calculation are retained; no molecular result is mocked.
The initial raw record is `query-dynamic-before-01` in the private A5 timing
workspace. A complete four-page issue inventory found no equivalent: #332
concerns saved-frame restoration and #333 playback pacing.

## How

Extend the trusted frame-query owner stamp and Python destination validation
from #337 to dynamic regions. Query replies carry complete memberships and a
local request ID. Keep the existing cached scientific evaluation, budget/freeze
warning and Python membership-update semantics. Coordinate-edit scene
projections remain separate from requester-owned answers.

The renderer rejects foreign IDs and mismatched frames before state writes.
An obsolete answer can finish its own pending query and request the current
frame without applying obsolete atoms. Legitimate uncorrelated scene edits
apply only at their actual current frame. Model replacement and managed partial
coordinate edits invalidate pending identities; the sequence remains monotonic.
Panel-only controllers do not request geometry.

## Why

The visible region and the saved frame must describe the same molecular
structure. Request ownership also avoids unnecessary native component updates
in unrelated canvases. The preceding popup-state/session passes do not receive
this new source, and this correction is not assumed to resolve every detached
Studio timeout before execution.

## Remaining receiving

The source retains the original ordered scene queue. Separate completion lanes,
follower pacing and coalescing were unsuccessful A5 experiments and were removed;
their source capsule and four failed native attempts remain preserved. Subsequent
traces identify the producer-side
[#339 box echo](../archive/applied_box_feedback_reprojects_geometry.md). The selected source
is receiving that direct correction together with the requester/frame guards.
Budget-triggered freezing publishes the complete static membership as a shared
scene change, separately from frame-scoped query answers, so a different-frame
renderer does not lose its frozen geometry.

The current combined Python selection passes 218/218. The selected early-model
query timing still fails native attempt 07, so that result does not establish
moving acceptance. The next source uses a bounded two-query window per family
and renderer: one previous frame can overlap the current frame, while additional
desired frames coalesce. Completion IDs retire only their own slot and cannot
mark obsolete geometry as applied. Two directed controls fail before this
change; the affected protocol entry then passes 12/12 and the canonical Node
entry passes 428/428 without skips. Native attempt 08 fails popup-state in
70.42 s with 4,329 unchanged selected inputs and full owned-process cleanup;
the three subsequent roles do not execute. The bounded window is not a received
solution for moving capture, and no moving acceptance is claimed.

The preceding affected Python selection passes 147/147; strict production TypeScript,
runtime/harness builds and all E2E builds pass. The canonical Node entry passes
424/424 without omissions. Its first execution passes 423 and fails the old
coalescing fixture, which constructed a controller without constructor fields
and expected frame-only replies. Initializing the new query identity and
asserting stale-ID rejection/monotonic replacement fixes the fixture; no product
fallback for uninitialized private fields is added. All earlier results remain
retained with their distinct source cohorts.

Run affected Python and canonical frontend checks, then unchanged native
popup/detached captures. Retain the original failures and the ten-second Studio
deadline, two observed owning-canvas frame changes, full native geometry,
independent saved-file restoration and source immutability. Capture version 2
remains unadvertised. A5 and mandatory Movie #320 remain incomplete under #315.
