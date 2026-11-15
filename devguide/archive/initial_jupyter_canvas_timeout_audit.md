---
summary: Require corrected Jupyter shell transport for initial molecular-canvas startup.
issue: uibcdf/molsysviewer#384
status: resolved
opened: 2026-11-13
closed: 2026-11-15
severity: medium
verification: reproduced
area: [jupyter, initialization, integration, receiving]
guard: tests/test_source_workflow_coverage.py::test_notebook_environments_require_the_corrected_native_shell_transport
normative:
blocked_by: []
supersedes: []
---

# Initial Jupyter canvas — accepted host-profile resolution

**Resolved technically — 2026-11-15:** Diego accepts the corrected Jupyter
host profile after the paired causal controls and normal TcTIM startup.
MolSysMT #615 is [closed with that accepted resolution](https://github.com/uibcdf/molsysmt/issues/615#issuecomment-6902474490)
in owner commit `5afa582f8cbd4b7c59c7be1fb05fb5063141ece4`. This completes
MolSysViewer's requested lead audit under #384. The original event's exact
cause remains unproven; the retained observations below are not rewritten.

## Resolution — 2026-11-15

The supported notebook host requires `ipykernel>=7.4.0`. Component source-test,
test, development and documentation recipes already declare that floor in
`f6765f6c`; `3aff1d48` adds the four-recipe regression named in `guard`.
It fails if a route loses the corrected minimum. This is a Jupyter profile
requirement, not a new mandatory dependency of core/headless or Qt use.

The demonstrated 7.3.0 shell notification loss, upstream repair and original
7.4.0 controls support this engineering resolution. Normal control `928`
receives the unchanged owner #762 guard on current committed MT source:
3,983 atoms and a new native draw in 10.7884 seconds, inside the original
30-second bound, without a scheduling barrier or artificial retry. The
[immutable receiving receipt](https://github.com/uibcdf/molsysviewer/blob/7d88b56a6514dc1509ae0cfb85bb77ca1b12c0c9/devguide/initial_canvas_edge_receiving_20261115.json)
retains actual loaded origins, source/native identity, original failures and
private custody. The normal-source condition is independently reviewed by
MolSysMT in `a1efa599a`; the principal maintainer then explicitly accepts it.

The minimum guard passes in all three native Python 3.14 source jobs in
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908),
which also receives all 63 core suites and 25 notebooks. This closure does
not infer the original missing transition, qualify installed/final artifacts
or complete postponed human review. The exact final-pair initial-scene guard
remains required. Controlled shared-prefix adoption belongs to MolSysSuite
#200; that existing prefix is unchanged. No package, tag or publication is
authorized by this technical acceptance.

## Earlier investigation and recommendation history

MolSysViewer led the investigation requested by the principal maintainer;
MolSysMT #615 retained its consumer/release dependency. The earlier
unresolved-risk proposal was not adopted, and the initial decision in
`c80e7380a` kept the issue open. The subsequent causal investigation and
accepted normal-source condition above supersede that pending state while
preserving the following dated evidence.

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
[#396](../archive/jupyter_movie_seek_pending.md). An associated environment inventory is
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

## Controlled initial-execute counterexample — 2026-11-15

Control `919` demonstrates that the ipykernel shell notification defect can
strand the **initial execute request before cell entry**, independently of
MolSysViewer, molecular imports, widgets, a browser or rendering. This is a
new causal control, not an uninstrumented recurrence or proof of the cause of
the preserved #615 attempt.

Two fresh kernels use the original isolated Conda providers, verifying all
57 selected provider files before and after each arm:

| Original provider | Archive SHA-256 | First cell-entry marker within 30 seconds |
| --- | --- | --- |
| ipykernel 7.3.0, `pyha191276_0` | `305ad9226363ff5f259c404dd9a7508183a2e150739b2adc43db7d817234da66` | Absent; the correlated execute never enters `dispatch_shell`. |
| ipykernel 7.4.0, `pyh4a3486f_0` | `9ea2c55f4a9aa9146f614f827412716c6f53cd08eace21297b687301b804bb97` | Present after 12.7 ms; the same request enters native dispatch. |

The diagnostic changes only scheduling. Each arm sends one real history
request. A bounded in-process delegate holds its real `history_reply` until
the first real execute is queued, then calls the original send exactly once.
It records real parent/request IDs and observes the native ZeroMQ descriptor
with `select.select`; it never reads `ZMQ_EVENTS`, manufactures a packet or
resends execute. The descriptor changes from not ready to ready before the
native reply send in both arms. After the original 7.3.0 send it is no longer
ready, yet execute has not entered dispatch. The 15-second native traceback
shows the shell event loop waiting in `select`, before molecular work exists.
The corresponding 7.4.0 arm dispatches and executes immediately.

The diagnostic's essential ordering is:

```python
# Diagnostic-only delegate around the original kernel reply method.
fd = shell_socket.getsockopt(zmq.FD)
before = bool(select.select([fd], [], [], 0)[0])
record_real_history_parent_and_release_the_client_to_send_execute()
wait_for_the_client_send_marker_at_most_two_seconds()
ready = bool(select.select([fd], [], [], 2)[0])
faulthandler.dump_traceback_later(15, file=private_stack)
return original_send(self, original_reply_parts)  # exactly once
```

Those descriptive recording/barrier helpers stand for the private program's
file synchronization; they are not product APIs or a replacement transport.
The original full programs, correlated timelines, provider origins, hashes
and traceback are retained under private custody referenced by the
[three-block receipt](../molstar_closeout_three_blocks_20261115.json).
[Upstream #1529](https://github.com/ipython/ipykernel/pull/1529) changes this
7.3.0 raw-socket send to the owning `ZMQStream.send_multipart` route; the
observed control is consistent with that released correction. The shared
prefix remains unchanged. The whole paired control takes 34.78 seconds,
peaks at 107.9 MiB under 1 CPU/1 GiB, preserves every selected input and
retires all three tracked processes without a resource stop.

The original #615 environment inventory reports the affected kernel version,
but lacks a loaded-module identity, actual history/execute overlap and
pre-deadline stack. Its symptom is compatible with this mechanism; causality
for that particular historical execution remains unproven. Keep #615 open.

## Next bounded work and closure

**Next discriminating control:** the original cell's first explicit work is a
45-second traceback prelude, followed by molecular imports, TcTIM construction,
coordinate/chemical-state/scene snapshots and the independent distance oracle,
then the final display expression. No entry marker survives from the failed
30-second attempt; its actual mutable client source revision is not recovered
from the associated host-version inventory. Do not call a current replay an
exact historical source reproduction.

The initial kernel-only transition is demonstrated in `919`; the paired
actual-browser diagnostic below receives the same mechanism with TcTIM.
Next, review that causal evidence with MolSysMT and the principal maintainer,
then receive the final candidate on its explicit corrected notebook baseline.
Do not retry unchanged diagnostics to accumulate passes or retrospectively
assign the original execution a missing observation.

The required full startup receiver still distinguishes actual preparation,
runtime-source exchange, controller/scene registration and a fresh native draw
of all 3,983 atoms. Keep historical causality, current source receiving and the
final installed candidate separate.

## Actual Jupyter/TcTIM overlap — 2026-11-15

Diagnostic `923` uses the real Jupyter client to request history, then clicks
the normal Run control once while that actual reply is held. Only the
scheduling delegate, bounded header observations and a first-line marker are
added. Owner tests come from MolSysMT `bc5a9297`, over unchanged scientific
source/native bytes from `aee7aa65`; this is a declared older scientific
composition, not final-source or installed qualification. The unchanged owner
receiver still requires the actual 3,983-atom scene and an eligible new native
draw within 30 seconds. The isolated loopback server exposes its real client
object for observation; no replacement client, product reply, warmed
molecular import or extended product deadline is used.

| Original kernel | Correlated execute: server send to kernel dispatch | Browser's original 30-second verdict |
| --- | --- | --- |
| 7.3.0 | 30,523.9 ms | Fails; no cell-entry marker, registered molecular scene or draw before the verdict. |
| 7.4.0 | 1.6 ms | Passes the complete owner startup entry; 3,983 atoms and a fresh post-registration draw 6,547 ms after the recorded Run click. |

The actual browser-send-to-server-send interval is 1.2 and 1.5 ms,
respectively. Both real socket edges qualify, with the actual history parent
and execute IDs retained. The old kernel's 15-second stack again waits in the
shell event loop, before molecular preparation. Its cell-entry marker appears
only **after** the browser verdict, during retirement; it does not repair that
failed attempt. Browser click-mark timing can lag the first kernel entry, so
do not interpret cross-boundary negative marker deltas as a latency metric.
Server-to-kernel admission and the native draw use their explicitly recorded
anchors.

Keep the original combined driver's **exit 1**: its final postprocessing
assertion expected the old marker to remain absent after retirement, rather
than checking entry before the deadline. The retained timestamps disprove
that expectation. Offline verifier `924` independently checks the unchanged
raw messages, unique correlated execute, server send, native admission,
pre-verdict absence, late marker and the new kernel's exact scene/draw. It
passes without rerunning either browser arm or rewriting their outcomes.
The old owner arm remains failed; the new owner arm's native exit is zero.

Preparation attempts `920` (non-executable private Node wrapper) and `922`
(Chromium's native Unix socket path limit under an overly long temporary
root) never reach the scheduling control. Both are retained as setup failures;
the wrapper permission and managed short temporary root are corrected before
`923`. They are not molecular recurrences or receiving passes. The paired
actual-host diagnostic takes 78.22 seconds, peaks at 2,364.0 MiB under
8 CPU/4 GiB, preserves all 9,980 selected inputs and retires all 53 tracked
processes without a resource stop. No shared environment is changed.

This demonstrates a concrete host mechanism producing the initial-canvas
symptom under controlled timing, and its absence in the matched corrected
provider arm. It does not measure spontaneous recurrence, authenticate the
original historical cause, qualify every platform or complete the final
installed candidate. **#384/#615 remain open** for that evidence review and
the applicable candidate receiving, rather than an unknown-cause waiver.

## Normal corrected-host receiving and joint recommendation — 2026-11-15

The joint review identified one distinct missing control: an ordinary TcTIM
startup on 7.4.0 without a forced overlap. Earlier `845`/`847` use the older
host; the corrected-kernel Movie control `916` uses 62 atoms. Neither replaces
this case. The [joint owner proposal](https://github.com/uibcdf/molsysmt/blob/0ff6af80a/devguide/pending_bugs/intermittent_jupyter_initial_canvas_timeout.md#joint-recommendation-requested-by-the-maintainer--2026-11-15)
keeps the issue open pending this result and the principal maintainer's review.

Normal control `928` now passes the unchanged owner #762 startup guard:
**3,983 atoms and a new eligible post-registration draw after 10,788.4 ms**,
inside the original 30-second bound. It uses no history injection, held reply,
timing barrier, modified kernel launcher or scheduling/server/comm delegate.
Only isolated provider selection and passive post-preparation provenance
recording are added to the private generated notebook. The actual kernel
loads original ipykernel 7.4.0; all 57 selected provider files are verified
before and after. No shared-prefix installation is performed.

MolSysViewer source base is `6f80cc915a9f44b6eb47ace336fa543c9e0b35e1`;
both scientific and receiver sources match MolSysMT `bc5a9297` through
3,707 Git-verified package/receiver/manifest files. The reused native backend
is the recorded `4ffb82e4…` binary from `aee7aa65`, with unchanged Rust/Cargo
inputs. This is exact isolated source receiving, not installed/ABI or final
artifact qualification. The [receipt](../initial_canvas_edge_receiving_20261115.json)
retains actual loaded kernel/core origins, native hash, complete draw marks
and private custody. Both the plain Jupyter control and molecular page have
the same single `No active debugger session` fingerprint; this is not a
zero-page-error claim. Output and observer errors are zero.

The native owner CLI and supervisor both exit zero. The complete control
takes 35.77 seconds, peaks at 2,346.1 MiB under 8 CPU/4 GiB, preserves all
9,983 selected inputs and retires all 27 tracked processes without a resource
stop. Initial preparation attempt `927` never starts a browser: the frozen
review directory lacks `pyproject.toml`, leaving the wrapper preflight
incomplete. It is preserved as a setup failure; exact committed metadata and
an executable/version preflight are received before `928`. Only one normal
browser attempt is credited.

**Recommendation ready for review:** close the technical host defect with
`ipykernel>=7.4.0` as the supported Jupyter baseline, retaining the original
failure and its unproven exact historical cause. The causal controls,
upstream correction, normal startup and the four-recipe minimum guard support
that engineering resolution; reconstructing observations that were never
captured is not required. This adds no mandatory core/headless dependency.
Shared legacy-prefix adoption remains MolSysSuite #200. Exact candidate,
installed, human and public-release gates remain separate. **No issue closure
or approval is inferred:** review the result with Diego before changing the
current open state of #384/#615.

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
