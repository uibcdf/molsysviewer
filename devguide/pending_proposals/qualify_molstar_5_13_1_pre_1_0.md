---
summary: Qualify public Mol* 5.13.1 before the 1.0 freeze.
issue: uibcdf/molsysviewer#372
status: active
opened: 2026-11-12
closed:
verification: measured
area: [dependencies, rendering, lifecycle, integration]
guard:
normative:
blocked_by: []
supersedes: []
---

# Mol* 5.13.1 qualification before 1.0

**Accepted 2026-11-12:** the principal maintainer explicitly advances controlled
qualification of public 5.13.1 before 1.0. This changes the timing of the 5.x
slice previously deferred under #115. The wider v6/ESM/workspace migration and
unqualified new capabilities remain post-1.0 under #115. Tags, packages,
promotions and both 1.0 publications retain their separate approval.

The [#369 assessment](../molstar_integration_review_20261112.md) supplies the
three baselines, capability matrix, native comparisons and migration rationale.
Its historical receiving qualifies neither this migration nor a new package.
This is an additional stream in #315, without changing its original 46 outcomes.

## Frozen inputs and recovery

The pre-migration source is `185b0ed7fdfc75dd20306edf8c989a7c87ac9f2b`.
Its declared/locked/installed provider is `^5.4.1` / `5.4.1` / `5.4.1`.
The target is exactly npm **5.13.1**, source/tag
`a4e9cc79415213263090ee47bf380d2a33e0118e` / `v5.13.1`, tarball SHA-256
`08e9292fb427bbebe9e1ecaef9e1b1066e2323dc4327e83692c4a5c3f14fff4e`.
Preserve the old manifests, native artifact, adapters and runtime hashes before
changing the local dependency. Resolve the new dependency closure in a separate
working directory first. The recovery route restores those reviewed source and
lock bytes, runs clean `npm ci` against that lock, and rebuilds with
`npm run build:runtime`; it never moves published artifacts or human notebooks.

Exact pinning is deliberate: the private component-cache adaptation rejects
unreviewed provider versions and source bytes. A permissive range would promise
builds that the adapter intentionally refuses. Revisit the pin when receiving a
published native replacement or a separately reviewed dependency update.

## Ordered execution and acceptance

| Step | Exit and evidence | Current state |
| --- | --- | --- |
| Q1 | Preserve old identities; inspect exact new artifact/closure; align Node >=22 build routes. | Source selected: exact 5.13.1, isolated closure and old source/lock/runtime hashes preserved; build and recipe routes use Node 22. |
| Q2 | Forward the complete native renderer tuple; qualify the exact-byte cache repair and font upload seam. | Source-received: tuple and independent complete Spin/Rock defaults; project/build guards, actual chemistry/cache lifetime and 475 units pass, including the later popup observer controls. Native Start/Stop and motion on completed draws pass. |
| Q3 | Compare default/explicit font quality, allocation and actual label readability; receive glyph pixels, context restoration and disposal. | Retain native default quality 3 and explicit choices. Corrected original-package allocations and glyph/style controls pass; GPU upload/pixel/restoration controls pass. Full/host/installed/human scopes remain separate. |
| Q4 | Receive native molecular identity/bonds/boxes/trajectories, rendering/picking, measurements/interactions, cameras and popups. | Partial: completed context-menu motion, controls/popup mirroring and Studio layout/trajectory controls pass; remaining core receiving is pending. |
| Q5 | Receive session/H5MSM, Movie/encoders/offline output, actual-host lifecycle and prolonged use with unchanged scientific assertions. | Partial: current persistent Studio passes in 729; native physical teardown, real Qt/GPU capture and actual-Jupyter lifecycle pass in 730/731/732. Actual-Jupyter full receiving fails a moving Python save's original five-second deadline in 733; retain and diagnose it before repeating. Movie, prolonged and covering exits remain separate. |
| Q6 | Consolidate applicable source/platform/browser CI, installed candidate and maintained compatibility documentation before freeze. | Pending; no public candidate or publication authorized. |

Use sequential bounded executions: build/type/backend checks at 2 CPU/2 GiB,
native browser work initially at 4 CPU/4 GiB, within the agreed 8 CPU/6 GiB ceiling and
the conservative shared-memory reserve. Preserve failed native controls and
actual input hashes. Neither a skipped browser nor a postponed human check is
acceptance. Diagnose failures before repeating or broadening their gate.

The resource pilot measured busy assigned cores and spare capacity elsewhere;
subsequent browser receiving uses 8 CPU/4 GiB, with the same reserve, zero swap
allowance and own-process cleanup. This is an execution ceiling, not an
exclusive machine reservation or a claim that every operation uses eight cores.

## Ownership and limits

The component-cache repair remains until #363 receives a published native fix;
5.13.1 still has the strong-key cache. Preserve chemical/saccharide semantics,
independent systems and backing-buffer lifetime controls. #344's font-upload
adapter also stays until a native replacement passes its actual pixel/lifecycle
controls. Never silently lower an explicitly chosen font quality.

MolSysMT retains scientific preparation, detectors, ChemicalStates and H5MSM
ownership. The migration must retain public source/structure indices, units,
raw row-vector boxes and reference-state bond semantics. New visual features,
v6 periodic transforms, remote certification and an API/Studio redesign are
outside this qualification. Automated source, installed artifacts, covering CI,
visible Qt and postponed human acceptance keep distinct receipts.

## Source receiving in progress — 2026-11-12

The isolated acquisition retains 302 lock records and the exact public npm
integrity; 275 platform-selected packages were installed with lifecycle scripts
disabled. The original 5.4.1 installation remains available for recovery. Node
22.23.4 builds the runtime, harness and browser entries and runs **473/473**
canonical unit cases with no skips. The prior source type/build selection
receives **14/14** cases against the selected 5.13.1 package.

The additional real-provider cache guard passes: native and repaired readers
give identical chemical/saccharide results for absent, empty and populated
component tables and both component-name sources. The unrepaired native cache
retains all five independent table/coordinate buffers; the repaired one releases
all five. The build manifest asserts actual package provenance. This is a
bounded cache control, not a claim about complete browser/host memory release.

Original failures remain evidence. Acquisition first rejected npm 12's
single-element metadata array until the exact-one response was handled. An
initial test fixture outside the JS package selected an unrelated ancestor
Mol* 3.38.3; moving it under the owning JS package and asserting the complete
native import origin corrected the receiving setup. Neither failure is counted
as 5.13.1 compatibility. A separate build attempt stopped on global swap
activity despite available RAM; its partial execution is not a passed gate.
The subsequent unchanged resource policy receives the successful checks above.

The source build hashes and raw controlled profiles are retained privately;
the consolidated receiving record will name their exact inputs, outcomes and
custody after the native migration checks. The rebuilt runtime remains a
development artifact, not a published candidate.

## Native migration findings — 2026-11-13

The ten-family original/recovered geometry control passes all assertions in a
236-second diagnostic at 8 CPU/4 GiB. The old 5.4.1 control already takes 179
seconds at 4 CPU/4 GiB. These differently bounded totals are not a controlled
performance ratio. Original 180-second failures remain preserved. The complete
22-controller geometry suite now has a scoped 360-second budget; individual
operation deadlines and scientific assertions are unchanged. The canonical
core lane still requires its own successful unoverridden receiving.

The first core run also finds a genuine API boundary: native Spin/Rock now
require an axis. The source takes their native parameter defaults and clones
the vectors, retaining the explicit speed and 20-degree Swing angle. Actual
menu Start/Stop, authoritative Python echoes and camera movement on completed
draws pass. The test stops each animation after checking it, preserving fixture
ownership instead of carrying active rendering into unrelated menu checks.

Three auxiliary defects are separately owned: #373 corrects the stale 53-suite
inventory (62 entries, 59 core before #377); #375 restores the terminal failure-exit
contract in eight entries; #374 corrects the old State/font comparison origin.
Its three provenance regressions and actual chemistry/lifetime guard pass,
alongside the seven runner checks. Corrected native comparisons match every
consumed native input to the original 5.4.1/5.13.1 tarball: 90/103 State/font
files for 5.4.1 and 71/96 for 5.13.1. The amended #369 receipt preserves the
original withdrawn claims and immutable custody, with corrected measurements.

Default quality 3 remains native: its 43,092,660-byte atlas is approximately
four times the previous 10,801,082-byte array. Explicit quality 1 and quality-3
bold/italic choices retain their native semantics. This is an atlas allocation,
not per-label, whole-host or GPU memory. The bounded controls do not establish
perceived image-quality equivalence or all-device performance.

The complete current library's 6,356 JS/declaration files match the original
5.13.1 tarball before core execution. The first attempt at that verification
was stopped before any browser suite because repeated gzip seeking was
inefficient; a sequential archive traversal receives the same files in 1.237
seconds. Its interrupted result is retained and is not a product failure or a
passed core gate. Full receiving remains in progress.

The interrupted core run `701` completes context-menu and controls/popup
mirroring. #377 separates the accumulated Studio layout and persistent-capture
scopes while retaining the complete historical direct entry. The inventory is
now 63 entries/60 core. Run `704` completes layout/downloads/card/catalogue/
lifetime and trajectory geometry in 156 seconds. Its persistent scope completes
primary, popup and detached-Studio state/session roundtrip assertions before
the aggregate 360-second timeout during the final camera-intent controls. It
does not qualify the unfinished scope. The live entry now has a bounded
600-second aggregate budget; per-operation deadlines and all assertions remain.
Eight runner controls and all entry
builds pass in `705`; no resource stop or surviving owned process is recorded.

Canonical live receiving `706` now completes that entire persistent scope in
365 seconds without a timeout override: primary/popup/detached state/session
roundtrips, exact camera/frame file bytes, same-ID owner isolation, genuine
stale-camera rejection, physical input/partial camera intents on completed
draws, reset/zoom/local-reset mirroring and all cancellation controls. It exits
0 with unchanged inputs, no resource stop, no surviving owned processes and no
cleanup errors. The two Studio scopes are received across `704`/`706`, not as a
single uninterrupted full-core pass. The remaining core, actual-host, CI and
installed exits are still open.

## Popup lifetime receiving — #378

Run `707` completes boxes/trajectories and the moving state/session/annotation
entry, then fails the unchanged closed-owner assertion. Isolated `709`
reproduces it with the real canvas popup as both save owner and renderer. The
[resolved report](../archive/popup_pending_capture_close.md) preserves the
diagnosis, native close-event control and incomplete runs. The source adds
early owner-bound observation, preserves polling and rejects late source
injection after closure. Complete types/builds and **475/475** units pass in
`718`. Canonical `725` then passes the whole lifecycle entry in 161 seconds,
including real canvas/panel retirement, pending-save cancellation, late-reply
refusal, transport loss, static freezing and pending View closure. Native exit
is 0, inputs are unchanged, resource stops are absent and cleanup has no error
or survivor. This closes the focused source defect; it is not full-core or
actual-host acceptance.

The bounded #379 correction stops unused native rendering in panel-only
Studio windows while retaining real parameter state and the active associated
canvas. All 475 units, native types and builds pass in `723`; `724` receives
the actual hierarchy, stopped-panel/active-canvas loops, shape-only addon
Render/Clear, remount and subsequent molecular loading. Canonical `729` then
receives the full current persistent Studio state/session, camera-intent and
cancellation scope, including nested panel loop assertions, in 350 seconds
without a timeout override. The original `726` instrumentation failure is
retained, with its corrected nested-controller observation built in `727`.
Broader core/host/platform/installed receiving remains pending.

The six completed core entries in `701`/`704`/`706`/`707` belong to their
recorded earlier migrated runtime. #378 changes popup lifecycle, so they remain
useful source evidence without becoming a full current-runtime/core pass.
The [consolidated partial receipt](../molstar_5_13_1_qualification_receiving_20261113.json)
records the new runtime, all attempted scopes and remaining exits.

Run `716` passes Ruff, formatting of 1,063 Python files, queue indexes and
517 build/compatibility/distribution/reporting/static-view cases; its original
input snapshot precedes the later observer refinement. Audit of the unchanged
new lock records zero known registry vulnerabilities. `713` starts no command
because the shared-CPU preflight refuses the requested ceiling; `714` is an
operator private-driver-path error before browser launch. Both remain evidence,
with neither counted as a product failure or a passed qualification.

## Actual-host receiving — 2026-11-13

`730` receives physical WebGL teardown after a real 62-atom scene with five
representations: 541 observed handles are live before disposal and none remain
live afterward. Context loss and native counters are kept separately; this is
not a universal CPU/GPU lifetime claim. `731` passes the existing full native
Qt guard on Wayland, NVIDIA Quadro M2000/ANGLE and WebGL2, including state/session,
moving/background, cancellation and constructor/close controls. `732` receives
actual Jupyter lifecycle: retired callbacks and weak native structure, model,
axis and coordinate buffer collection, while an independent witness continues.
Their own process cleanup is clean and inputs are unchanged. These automated
host results do not replace postponed human or installed-package acceptance.

Full actual-Jupyter `733` completes six ordinary capture/restore cases, six
strong restore controls, four Studio cases and one moving capture, then fails
`Moving Python notebook state` with `FrontendRequestError(request_timeout)`
at the unchanged public five-second deadline. The kernel heartbeat progresses,
its comm remains open and molecular transfers are inactive; browser diagnostics
show moving-frame dependencies that do not converge before expiry. This does
not yet establish the cause or an upstream regression. The closed #344 history
and exact native event ordering need comparison before changing code, reopening
a report or repeating the guard. No resource stop occurs, selected inputs are
unchanged, and process cleanup leaves no survivor or error. Preserve the failed
gate rather than counting its completed subcases as complete receiving.

The independent [#380 PNG routing defect](../pending_bugs/detached_studio_png_uses_empty_canvas.md)
also remains pre-1.0 work. Main-canvas PNG receiving does not cover a detached
panel's associated-renderer route.
