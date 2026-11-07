---
summary: Trajectory-shape refreshes can discard the newest requested frame.
issue: uibcdf/molsysviewer#328
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [trajectory, shapes, capture]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Trajectory shapes after overlapping frame refreshes

The handler updates its desired frame, then discards a refresh if an older
one is still applying. A held asynchronous clear reproduces final frame 1
after frame 2 has been requested. The original unit selection has fourteen
passes and one genuine assertion failure; its renderer is replaced only to
isolate scheduling. The native geometry receiving is recorded below.

The complete four-page inventory contains 326 issue/PR entries and 298 issues.
Closed #238 concerns cross-canvas playback clocks/final convergence; #118
concerns coordinate-edit invalidation. Neither reports the dropped per-handler
refresh. This is a bounded prerequisite of A5/#319 under #315, not another
progress-denominator item.

Keep one bounded refresh owner and a latest-frame target. Duplicate requests
must share outstanding work; after an older refresh finishes, apply the latest
target without retaining an unbounded tick queue. Preserve nullable frames,
all existing trajectory-shape families and effective-status notification
deduplication. A capture reader must distinguish applied geometry from an
update still in progress. Receive this through real Mol*/molecular-fixture
geometry before closure; protocol tests alone cannot establish that result.

## Resolution — 2026-11-07

The correction keeps one refresh promise and catches up to the newest target
after an outstanding clear/render completes. Initial shape creation obtains the
actual molecular frame, and a private readiness reader rejects an unfinished or
failed update. Effective-status notification deduplication remains unchanged.
The directed selection passes all seventeen native Node cases, including the
original failing-before scheduler case, repeated latest-frame requests, failure
retirement/recovery and first creation on a nonzero frame. These assertions
isolate the scheduler. All 374 cases in the canonical Node entry pass.

The public Python fixture creates real pentalanine trajectory spheres from
coordinates and atom participants. The previous runtime fails the native
overlap assertion: the model reaches frame 2 while the coordinate sphere
retains frame 1's centre. The corrected runtime passes that identical geometry
requirement and first creation at frame 2 on a shape-free controller. Actual
mesh vertices and molecular coordinates are read on completed Mol* draws;
neither renderer geometry nor host replies are substituted.

The full registered Studio entry passes in 210.33 seconds, preserving its
existing primary/popup/detached save/restore, cancellation, camera authority,
PNG/HTML and lifecycle cases. All 4,303 selected inputs remain unchanged;
nineteen owned processes close with no survivors or cleanup/tracking errors.
The [receiving record](../trajectory_shape_refresh_receiving_20261107.json)
keeps the failed-before result, corrected native runs, exact source hashes and
validation scopes. Protocol 1 still rejects moving scene/frame recipes; this
bounded correction does not close A5/#319, change 8/46 progress or qualify a
new installed artifact, actual Jupyter campaign, native Qt run or release.
