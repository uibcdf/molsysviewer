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
| Q2 | Forward the complete native renderer tuple; qualify the exact-byte cache repair and font upload seam. | Source-received: tuple and independent complete Spin/Rock defaults; project/build guards, actual chemistry/cache lifetime and 491 current units pass, including image ownership/readiness and popup observer controls. Native Start/Stop and motion on completed draws pass. |
| Q3 | Compare default/explicit font quality, allocation and actual label readability; receive glyph pixels, context restoration and disposal. | Retain native default quality 3 and explicit choices. Corrected original-package allocations and glyph/style controls pass; GPU upload/pixel/restoration controls pass. Full/host/installed/human scopes remain separate. |
| Q4 | Receive native molecular identity/bonds/boxes/trajectories, rendering/picking, measurements/interactions, cameras and popups. | Partial: completed context-menu motion, controls/popup mirroring and Studio layout/trajectory controls pass; remaining core receiving is pending. |
| Q5 | Receive session/H5MSM, Movie/encoders/offline output, actual-host lifecycle and prolonged use with unchanged scientific assertions. | Partial: current persistent Studio passes in 729; native physical teardown, real Qt/GPU capture and actual-Jupyter lifecycle pass in 730/731/732. #381 separates healthy public defaults from deliberately delayed science; complete eight-case actual-Jupyter receiving passes in 739, with prior failed scopes retained. Movie, prolonged and covering exits remain separate. |
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
not establish a broken product deadline or an upstream regression. `736`
completes the original scope without a product fix; timed `737` then shows the
fixture withholding real queries for 3.82 of the five available seconds.
The [focused #381 correction](../archive/jupyter_moving_fixture_deadline_budget.md)
separates two healthy unchanged-default captures from all six delayed-query
controls at an explicit ten-second budget. Complete actual-Jupyter `739`
passes all eight, plus stopped/strong restores and cancellation/expiry, in
232 seconds. Its exact original inputs precede the new 300-second full-profile
aggregate bound; no individual product default is raised. No resource stop occurs, selected inputs are
unchanged, and process cleanup leaves no survivor or error. Preserve the failed
earlier gates rather than relabelling their successful subcases as completion.

The [#380 PNG routing correction](../archive/detached_studio_png_uses_empty_canvas.md)
and [#379 loop exit](../archive/panel_only_native_loop.md) now pass current
native receiving in 762: primary and nested origins, exact native RGBA
references, transparent/opaque output, independent owners, cancellation and
closed-origin refusal. [#382](../archive/native_image_asset_readiness.md) waits
for actual SMAA uploads before the first PNG/Movie draw. An independent
ordinary-export control reproduces the old cold/repeated distinction; the
corrected first/repeated output agrees without a warm-up or quality reduction.
The whole eight-image workflow has a 240-second bound after observed 172-second
receiving; operation deadlines are unchanged. Source type/build and all 490
units pass in 761; 763 receives panel/addon and native Movie export regressions.
The build rejects unreviewed bytes for the read-only native readiness seam.
Earlier failed controls remain evidence; full-core/platform/installed gates
and the architectural review remain open.

## Source checkpoint failure and scoped recovery — 2026-11-13

Exact-source run `43513962722` on published `6e13bd26` fails all three Python
3.14 jobs: Linux/macOS each have five shared guard/example failures and
Windows has eighteen, including twelve native-source UTF-8 decoding failures
and one real WebM encoder failure. The four original artifact ZIPs match
GitHub's size/digest inventory. Browser and notebook gates did not execute;
the uploaded pre-existing notebook logs do not qualify this source.

The [terminal receipt](../molstar_source_checkpoint_20261113.json) records
every failing node. Corrected source/coverage/vocabulary/encoding and page
controls pass **860 cases**, with four unselected actual-host skips, in `771`.
The connected-Jupyter example is explicitly named and received by the actual
kernel, rather than executed headlessly. #169 is reopened for new unspecified
reads; #385 owns native Windows WebM diagnosis. No format or pixel assertion
is removed. A scoped source-only Windows diagnostic is distinct from the next
full matrix and installed qualification.

Actual Jupyter `772` executes that exact live cell and completes six stopped
roundtrips, six strong restores, four Studio captures and six moving cases.
Global swap activity then crosses the conservative supervisor threshold and
our processes are retired cleanly. The resulting closed-browser observation
is an interrupted resource-controlled attempt, not an established product
failure. Its two remaining popup moving cases and final cancellation/expiry
remain unreceived. Own cgroup memory peaks near 2.35 GiB under its 4 GiB limit;
about 12.81 GiB remains globally available, without OOM or owned survivors.

After a fresh observation finds zero swap activity/pressure and 15.19 GiB
available, `774` receives the complete actual-Jupyter full profile on published
`26f935f0`: all eight moving cases, six stopped captures, six strong restores,
four Studio captures and final cancellation/expiry, including the exact live
documentation cell. Native exits are zero, selected inputs are unchanged and
cleanup has no survivor/error or resource stop. Actual cgroup memory peaks
at 3.04 GiB under the unchanged 4 GiB bound; summed process RSS is recorded
separately. This completes that host scope while preserving `772`.

The single Windows diagnostic `43521107544` uses the same published commit
and provider. It selects the real encoder module only and retains bounded
native stderr/identity plus its original logs. Its result cannot qualify the
full three-platform matrix; the original `43513962722` remains failed.

Windows diagnostic `43521107544` terminates with one failure / 23 passes
and no skips. Its original stderr identifies absent `libvpx-vp9` in the
selected FFmpeg 9.0.2; the exact native digest and original artifact ZIPs are
retained under #385. The inspected conda-forge recipe explicitly excludes
libvpx on Windows. Codec policy/availability needs an explicit decision and
native receiving; no new Mol* regression is established by this result.

Full-core local `775` receives one complete context-menu suite, then global
swap activity (95,244,288 bytes over about five seconds) crosses the safety
threshold during controls/popup receiving. All own processes are retired,
inputs remain unchanged and the original attempt stays interrupted. Its
4 GiB cgroup peaks near 1.84 GiB, with about 10.04 GiB globally available
and no OOM. Do not infer full or two-suite acceptance from partial controls
logs. A fresh extensive local run is postponed while this shared-resource
pressure recurs; final full-core and hosted platform gates remain required.

Actual Movie notebook `770` separately passes all eight cases after the #383
field-label correction. Retain its original failed `767` attempt and exact
owner inputs. Neither this successful host nor local checks make the failed
source checkpoint green or close #369/#372.

## Current codec recovery — 2026-11-13

The [codec receipt](../movie_codec_receiving_20261113.json) implements explicit
and automatic native selection for #385, after Windows diagnostic stderr
establishes absent libvpx. Final local sources receive 776 Python passes,
491 canonical JS cases and native Studio AV1 export/browser playback.
The ordinary Movie-export and shape-only/popup regressions also pass. The
additional #383 receiver label is corrected and guarded across both owners;
earlier actual-Jupyter receiving retains its original source identity.

The 320p chromatic-edge oracle failures and independent codec-free YUV420
control remain preserved. The final 720p interior-colour guard uses the
existing MP4 sampling rule and unchanged tolerance; product quality and
deadlines are unchanged. The [terminal source receipt](../source_checkpoint_recovery_20261114.json)
receives all 61 codec/export cases on each source host, including Windows
automatic AV1 with the exact formerly failing executable, and all twelve
original Unicode cases on native Windows. #385/#169 are source-resolved.
The complete checkpoint remains failed by #386's command/path guards;
Linux core/notebooks were not reached. A notebook-log artifact is proved to
contain tracked history despite its executor being skipped; its producer
condition is corrected. Receive the new complete source/core gate after the
scoped repairs. No installed artifact is qualified.

## Current covering and prolonged receiving — 2026-11-14

The [followup receipt](../molstar_qualification_followup_20261114.json)
receives all three native Python 3.14 source hosts (4,724/4,693/4,697 passes)
and all 25 Linux notebooks on `22b51f89` with scientific provider `aee7aa65`.
Original artifact sizes and hashes agree independently. #386 is source-resolved;
the complete run `43616029893` remains failed by reopened #244.

That recurrence exhausts the combined controls entry after its two earlier
workflows, while its independently initialized scientific mirror is still
progressing. The mirror now owns a separate mandatory core entry with the
same 300-second budget. Every original scientific assertion, operation wait
and cleanup is unchanged; only per-camera phase timing is added. Native
`802` passes both complete entries without overrides. The build and 535
source guards pass in `801`. Inventory is 65 total / 62 core entries; all
three remote preview entries retain their post-1.0 exclusion.

The complete uninterrupted core lane remains required. Prolonged receiving
uses the unmodified canonical MolSysMT #723 method at `429d7494` over the
frozen `aee7aa65` scientific/native source, recording that composition rather
than claiming a pure provider checkout or an installed pair. Its retained/
released-object and remote-handle control passes in `800`; the plain-Jupyter
baseline, one-cycle pilot and current 30-cycle session are separate exits.
The first harness attempt has a too-long Chromium socket path and no executed
molecular gate; its failure is retained. Managed short temporary paths correct
only that launcher limitation. None of these controls changes scientific
algorithms, silently disables a Jupyter extension or replaces human acceptance.

Full-core `804` then receives the first three complete suites, including both
new mandatory owners, before global memory PSI full `avg10=5.68` crosses the
unchanged safety threshold 2 during Studio. All 39 owned processes retire,
inputs remain unchanged and no OOM, swap activity or owned cleanup error is
recorded. Available RAM is 15.16 GiB and own cgroup pressure remains zero;
those observations do not identify the cause of global pressure. The child
status zero does not qualify the interrupted lane. Preserve three complete
suites and one incomplete scope, then use the next substantive hosted checkpoint
for the whole core lane instead of repeatedly loading this shared host.
