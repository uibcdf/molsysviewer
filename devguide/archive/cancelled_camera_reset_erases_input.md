---
summary: Cancelling a pending camera reset can overwrite input applied before scene commit.
issue: uibcdf/molsysviewer#335
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [camera, input, popup, synchronization]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Deferred cancellation preserves physical camera input

**Resolved:** bounded correction received; see the final section and shared receipt.


The first canonical split Studio execution passes all six state/session restore
routes, then times out after 30 seconds waiting for a real popup drag to change
the camera after stopped drawing restarts. The run exits 1 in 339.81 seconds,
with 4,322 fixed inputs, eighteen owned processes closed and no pressure stop.
This is separate from #334's accumulated-entry timeout.

The pending-intent abort saves a static snapshot before native controls apply
the drag. Molstar 5.4.1 `PluginAnimationLoop.start` calls `resetTime`, whose
`controls.start` consumes accumulated input before the next canvas commit.
That commit then applies the older cancellation snapshot, erasing the input.
A one-case guard with the real native Camera and existing controller/sync
fixture reproduces this order: the accepted `[100, 0, 0]` pose becomes
`[0, 0, 100]`. Native result: zero passes/one failure; one CPU/1 GiB.

The working correction keeps cancellation ownership and retires the old
transition, but resolves the preserved native pose at commit. The prior unit
case now asserts retained behavior without requiring a static snapshot, and
the delayed-controls case guards the missing ordering. Receive the complete
camera unit entry and actual native physical input/navigation with unchanged
assertions and deadlines before closure. This mechanism does not prove that
every older capture timeout shared its cause.

The first passive diagnostic attempt separately fails while reading a
nonpublic controls property. Its 255.24-second exit 1, 4,320 fixed inputs and
fourteen closed processes remain preserved. Instrumentation now reads the
public trackball/camera state and preserves the original exception even if a
secondary observation fails; that diagnostic repair is not a product fix.

Complete issue acquisition: four pages, 100/100/100/33. #319 owns wider capture
acceptance; closed #177 concerns Movie interruption. This is a bounded A5
prerequisite under #315 and does not add another original-plan leaf. Both
1.0 publications, tags and packages remain paused.

The canonical Node entry passes 406/406 after the correction, including the
new delayed-controls case. The prior immediate-cancellation control starts
with a valid radius of one and retains full applied snapshot equality; the
first expanded run exposed native normalization of its previous zero radius
to 0.01. That 405-pass/one-failure run remains distinct from the later complete
406-pass result. Every runtime/harness/E2E build passes; native receiving of
the corrected physical-input path remains required. Current check receipts use
a create-only directory after the documented local log-name reuse incident.

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
