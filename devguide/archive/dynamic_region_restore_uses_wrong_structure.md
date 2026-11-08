---
summary: Dynamic region recovery evaluates its recipe against the wrong trajectory structure.
issue: uibcdf/molsysviewer#332
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [regions, persistence, trajectory, capture]
guard: tests/test_moving_state_capture.py::test_dynamic_region_recovery_uses_the_saved_structure
normative:
blocked_by: []
supersedes: []
---

# Dynamic-region recovery at the saved structure

**Resolved:** bounded correction received; see the final section and shared receipt.


The real A5 empty-frame guard now reaches and saves structure 1 after the #331
working correction. Its native dynamic component is empty and the captured
frame is correct. Independent headless `new_view(...); load_state(...)` returns
that frame but materializes atom 1 from structure 0. The run exits 1 after
20.66 seconds, with 4,319 fixed inputs and thirteen owned processes closed.
This is `5390fadb` plus the working receiver/presentation/navigation changes,
not qualification of an unchanged published artifact.

`_restore_region_v2` evaluates a retained dynamic recipe without a structure
index; `_restore_view_state` sets the saved index later. The imported recipe,
membership and visible structure must agree before a Python consumer can read
the recovered View. Supplying the saved frame while materializing a dynamic
recipe avoids storing memberships for every structure or changing coordinates.

The complete four-page issue inventory and newly opened #331 were checked.
Closed #189 retained a static empty snapshot after a 25-ms fallback; #307
corrected numeric selections becoming all. This retained dynamic recipe's
wrong evaluation structure is different. It stays inside A5/#319 and #315,
with the original denominator unchanged.

Receive state and session files, saved empty/nonempty structures, an existing
target initially at another structure, dynamic identity/mode and unchanged
explicit/static membership. Keep dependency recipes, isolation, normal live
updates, units and headless behavior. The separate moving-session timeout
remains unresolved; source inspection alone does not identify its cause.

## Working correction and directed receiving

Six real-demo controls reproduce two failures (the empty saved frame in state
and session), with four passing nonempty controls. Import now determines the
eventual valid player frame before materializing regions and passes it only
to dynamic-recipe evaluation. It does not navigate early, publish callbacks
early, copy trajectories or change static membership. Existing target frame
and normal saved-index handling remain explicit; the ordinary player/camera
restoration order is retained.

The unchanged six controls then pass in 7.65 seconds, preserving recipe UID,
dynamic mode, empty/nonempty membership and an independent static region.
The run uses a single systemd scope limited to two CPU, 4 GiB and no swap,
with a preceding resource observation and no other owned intensive run.
Legacy-H5MSM warnings remain visible. Wider state/region receiving and the
complete canonical browser entry are still required before closure.

The broader dynamic-region/isolation/state-v2/moving-state selection passes
115/115 in 45.91 seconds, retaining 152 warnings. It runs within a one-CPU,
2-GiB scope with one scientific-library thread after a fresh margin check.
The complete browser scenario subsequently passes after the separate playback
pacing correction (#333). In 36.20 seconds it receives moving state/session
and the empty saved frame through independent recovery, with all 4,319 inputs
fixed and thirteen owned processes closed. Applicable legacy receiving and
delivery remain pending; neither result is a release qualification.

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
