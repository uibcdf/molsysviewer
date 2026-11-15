---
summary: Serve immutable runtime-source replies independently of scene ownership.
issue: uibcdf/molsysviewer#392
status: resolved
opened: 2026-11-14
closed: 2026-11-14
severity: medium
verification: reproduced
area: [jupyter, bootstrap, concurrency, lifecycle]
guard: tests/test_runtime_source_scene_ownership.py
normative:
blocked_by: []
supersedes: []
---

# Runtime source and scene ownership

**Resolved in source — 2026-11-14:** the causal guard and actual-kernel
receiving below pass; final hosted/installed acceptance remains separate.

The [#384 startup audit](../pending_bugs/initial_jupyter_canvas_timeout_audit.md) reproduces
a distinct current defect: both `request_widget_runtime_source` and
`request_popup_source` raise `SystemEditPendingError` when another thread
owns the molecular scene lock. The same calls return after release. Their
source responses already bypass structural application and are permitted
while managed edits are pending, but the outer lock rejects them first.

The response is immutable bundled JavaScript, independent of molecular
indices, the current scene and `_ready`. The browser cannot finish loading
its runtime without that response. Direct widget mounting exercises this
branch; the normal notebook presentation surface has a separate source
reply and shared runtime cache. Do not claim that either the current
counterexample or its correction explains the original #615 timeout.

Private profile `840` records the real demo/control-handler failure without
a replacement transport. Profile `841` then fails precisely the two new
contended-source regressions; the three closed-view/mutable-command controls
pass. After the fix, all five pass in `842`. Native errors, original source
hashes and expected legacy-demo H5MSM warnings remain preserved.

The handler now replies only to these two source requests before acquiring
scene ownership, on its existing connector caller thread and only while the
View remains open. It neither schedules an arbitrary sending thread nor
weakens scene locking, structure ordering or source-envelope rules. The
regression uses a real demo and worker-owned scene lock; its outgoing observer
delegates every send to the actual connector and records only op/digest/thread.
State, history and ready status stay unchanged.

Receive the affected Python boundary and a real cold Jupyter start, including
a deliberately contended direct-widget path with an observed actual source
reply. Keep that generated fixture extension explicit; it is not the untouched
default presentation flow. The running full CI `43654425383` remains on
`2947c2fd` and does not qualify this later Python correction. No runtime rebuild
is required, and installed/candidate/human acceptance stays separate.

The [receiving record](../initial_canvas_audit_receiving_20261114.json)
retains the five causal controls and all 38 affected Python cases (overlapping
the five), plus real fresh-kernel normal and contended direct-widget starts.
Both register 3,983 atoms and a new eligible native draw; the contended source
reply is observed while the worker owns the scene, before ready and on the
actual connector callback thread. That thread differs from initial-cell
execution. All inputs remain unchanged and all owned processes retire.
Original receiver-observer failures `844`/`846` remain preserved: incorrect
public-class source attribution, then an incorrect initial-cell-thread
assumption. Neither is claimed as a product failure. #384/#615 remain active.
