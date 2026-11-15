---
summary: Audit the initial Jupyter molecular-canvas timeout with phase-specific evidence.
issue: uibcdf/molsysviewer#384
status: active
opened: 2026-11-13
closed:
severity: medium
verification: measured
area: [jupyter, initialization, integration, receiving]
guard:
normative:
blocked_by: []
supersedes: []
---

# Initial Jupyter canvas — MolSysViewer leads the audit

**Active pre-1.0 requirement.** MolSysViewer owns the investigation requested
by the principal maintainer; uibcdf/molsysmt#615 retains its consumer/release
dependency. MolSysMT's [owner handoff](https://github.com/uibcdf/molsysmt/issues/615#issuecomment-6866859272)
does not establish a product-code cause. The earlier unresolved-risk acceptance
proposal was not adopted. A later passing attempt is not a causal correction.
The [existing integration handoff](../molsysmt_pre_1_0_handoff_20261110.md#molsysmt-615-first-canvas-evidence)
retains the diagnostic contribution and its original source scope.

## Original evidence reinspection — 2026-11-14

The original three-scenario attempt's Analysis step fails before its panel
opens, after the unchanged 30-second visible-canvas wait. Its raw failure JSON
SHA-256 is `f7bfe46f2da867e9768cf031a37b503fe3413d5d43af16e0ce2270957455701d`;
the retained DOM SHA-256 is
`60bfc5a18d56fcce0b093c9aa9cc96806bfd48c8f477d336f369bc2080cd6838`.
No Analysis checks complete. The DOM shows `[*]`, no displayed molecular
output and no explanatory Python exception. Its zero-byte stack file uses a
45-second timer, later than the failed wait. That prelude does not write an
initial marker: an empty file therefore does not establish that execution
never began, finished, or stopped in any particular library.

A separate earlier setup attempt has failure JSON SHA-256
`0d1bb0b95638d8a14334751427bfbf5acf541082ba6d86ce6f8737d1339d995a`
and DOM SHA-256
`ecb9d9faeeebfc09cc69ca2761ec80605237fade002a2457e62bd5a734437fdf`.
It completes the cell with a NumPy broadcasting `ValueError` in the fixture's
distance oracle, before its final `view` expression. Its input differs from
the corrected Cartesian oracle used in the three-scenario attempt. Keep this
known preparation failure separate from #615; do not interpret both canvas
waits as missing runtime delivery or a common product failure. MolSysMT #754
now owns the general receiver error/phase-attribution correction.

The subsequent initialization diagnostic writes both start and completion,
finishing its initial cell in 3.357631 seconds. That is useful later evidence,
not a reconstruction of the original missing phase or an accepted resolution.
The original files remain private and unchanged.

**Retained environment supplement — 2026-11-15:** the same original failure
directory still contains `environment.json`, written before its failure JSON.
Its SHA-256 is
`f460e8b970e9c71c6fb6ec32a3b9f6b51ff9144e8584002b13b0ddc1a14f6b98`
and its installed-package inventory reports ipykernel 7.3.0. The neighbouring
failure still matches the original `f7bfe46f…` digest above. The independently
reproduced newer comm stall and 7.4.0 source-host solution are tracked under
[#396](jupyter_movie_seek_pending.md). An associated environment inventory is
not an observation of the module loaded in the original kernel, nor proof of
its missing transition. Neither failure is relabelled. A separately hashed
private supplement preserves both originals; the current closure receipt
records that custody and the owner handoff without a new execution.

## Current startup path and discriminating observations

| Boundary | Current owner and ordering | Evidence needed before attributing a failure |
| --- | --- | --- |
| Python preparation | `new_view` creates a View, then synchronously loads/converts the supplied molecular system. The Analysis fixture also snapshots chemistry/scene and computes its independent oracle before its final display expression. | Cold import, demo-load and pre-display markers, exception and completion; original requested molecular/source identities. |
| Notebook display | `MolSysView._repr_mimebundle_` presents the host surface; its small AnyWidget bootstrap requests the runtime through the widget comm. | Display-expression/post-run boundaries, actual model/surface identity and whether bootstrap was requested/answered. |
| Runtime acquisition | `widget.py` subscribes before requesting source; the shared cache is keyed by the runtime digest. The existing 15-second source deadline is distinct from the receiver's 30-second canvas deadline. Python deliberately answers source before `_ready`. | Actual source request/reply/import outcome; a cached runtime is not a cold import or proof of a reply for this attempt. |
| Controller and molecular projection | `index.ts` starts controller creation and sets up its ready/receive paths during render initialization; Python's `ready` handler chooses binary projection or JSON fallback. Received scene commands await the controller and structural application. | Mount/controller identity, ready/projection/ack progression and expected 3,983-atom scene registration. A bare canvas is insufficient. |
| Native drawing | Mol* scene registration precedes a new eligible `didDraw`; cached BehaviorSubject values are excluded. | A connected canvas belonging to the initial cell, positive visible representation/bounds and a new completed draw after registration. |

The source audit additionally reproduces [#392](../archive/runtime_source_replies_require_scene_lock.md):
immutable runtime-source requests are rejected when another thread owns the
scene-edit lock. A real demo counterexample and two causal failing regressions
establish that separate defect; the correction passes all five new controls.
The normal presentation surface's own source response/shared cache is a
different route. Neither this counterexample nor its fix establishes the
unrecorded historical concurrency or the cause of #615.

## Next bounded work and closure

Reuse the owning cold Analysis diagnostic and its actual kernel/session/browser
timeline, with unchanged deadlines and no warmed molecular imports. Receive
current source identities and targeted startup/transport controls before a
bounded actual-host attempt. MolSysMT has now closed #754 in published commit
`c4fa8552e9696ee225dd9abd51be4e2e441228c4`, with its manifest-cell/request/socket
error observer and expected/observed controller binding. The [independent receiving](../receiver_754_independent_receiving_20261114.json)
now passes those 72 selected tests, including nested Node and actual plain
Jupyter; six controller controls remain explicitly synthetic. This qualifies
the receiving tools, not a diagnosis of #615/#354. Consume that committed
receiver in a frozen snapshot rather than duplicating it or editing the owner
worktree. If a current startup hole is
reproduced, give it its own causal regression and keep applicability to the
historical observation explicit.

Closure requires the causal diagnosis/regression or a concrete evidenced
disposition reviewed by the principal maintainer, returned to MolSysMT #615.
Keep #305's later context-menu wait, #354's pre-save frame assertion and
server-readiness #705 distinct. No original outcome, candidate, installed
qualification or publication is credited by this audit record.

**Current source receiving:** the [receipt](../initial_canvas_audit_receiving_20261114.json)
receives the #392 causal fix and actual normal/contended kernel paths on
unchanged scientific/native sources. New native draws occur 6.39 and 6.89
seconds after the observed Run click, with exact loaded-handler provenance.
These are two measured controls on the declared host, not a universal latency
guarantee. Fresh servers/kernels do not clear OS/disk caches. Original #615
causality/disposition is still required; its source outcome is not credited.
