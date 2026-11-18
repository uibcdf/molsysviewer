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

**Reaffirmed 2026-11-14:** after reviewing v6's development and unpublished
package status, the maintainer keeps v6 post-1.0 under #115. No v6 pilot or
migration is added to this qualification. Complete the selected public 5.13.1
scope and its outstanding source/installed exits without waiting for v6.

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
| Q4 | Receive native molecular identity/bonds/boxes/trajectories, rendering/picking, measurements/interactions, cameras and popups. | Current Linux source receiving: 63/63 core suites in 44370662706 on 95d87988/4b0b1f8a, including DataCard, all interaction calculations and Movie. |
| Q5 | Receive session/H5MSM, Movie/encoders/offline output, actual-host lifecycle and prolonged use with unchanged scientific assertions. | Current source scopes received: earlier named-session/H5MSM, Movie/encoder/offline and actual-host controls retain their exact inputs; canonical default-Jupyter reference and retained/released controls pass, followed by 30/30 same-kernel cycles in 809 on a72c92ba. Covering and installed acceptance remain separate. |
| Q6 | Consolidate applicable source/platform/browser CI, installed candidate and maintained compatibility documentation before freeze. | The earlier three-host baseline and the current full Linux source follow-up are verified. The exact installed pair and remaining compatibility and host exits are pending. |

## Current closeout checklist — 2026-11-15

The technical assessment and source corrections are delivered in their declared
scopes. Closing this qualification still requires these three exits:

**Changed-source follow-up — 2026-11-17.** Run
[44176403184](https://github.com/uibcdf/molsysviewer/actions/runs/44176403184)
passes Python, 25 notebooks and the first eleven core entries, including
moving capture, lifecycle and popup bootstrap. The 180-second limit of
`studio-list-workflows` stops entry 12. A local action trace reproduces that
limit while assertions continue to pass. At the same resource ceiling the
unchanged suite passes in 291 seconds with a 360-second aggregate allowance.
Only that entry receives the measured allowance and progress markers.
The [receipt](../moving_capture_followup_receiving_20261117.json) retains the
original failure, local inputs and log digests. Complete hosted receiving of
the changed source is pending.

On `6cced30f`, local receiving `1058` passes all nine selected core suites
in one Chrome process with the runner's default limits. This covers Studio
saved lists and the next eight entries in the hosted order, including
annotations, native arrays, source indices, coordinate edits, composite
loading and popup lifecycle. The runtime digest matches the reviewed
`d8c10784` runtime. The same [receipt](../moving_capture_followup_receiving_20261117.json)
keeps the current local pass and the earlier hosted timeout on their
respective inputs.

Further local checks on `6cced30f` receive DataCard lifecycle and the full
trajectory-plot entry, including the independent static page. The supervisor
retires that browser group during Movie when shared full-memory pressure
crosses the safety threshold. After pressure subsides, the isolated Movie
story passes in 319 seconds at 4 CPU / 3 GiB under the default suite limit.
It checks the real producer and restored import origins against the frozen
files, retains exact scientific signatures, compares decoded PNG/MP4/WebM
pixels and completes offline playback. These twelve local suite passes
support the next complete hosted source checkpoint. The receipt keeps the
earlier resource interruption and all three local invocations.

The maintainer-authorized [Linux source checkpoint](https://github.com/uibcdf/molsysviewer/actions/runs/44196971862)
on `43c1c3de` and `4b0b1f8a` with pandas 3.1.0 passes 4,756 Python tests,
25 notebooks and 33 core suites, including Studio saved lists. Entry 34,
`font-atlas-uploads`, passes its eight native atlas/resource checks. Its
molecular trajectory case observes three uploads against an expected zero.
The run's official conclusion is failure. The terminal log and both original
ZIPs are verified. The dispatch inventory contains exactly one matching run.

The isolated real-browser control `1066` reproduces all three measured
uploads. In `1067` they occur on the first measured frame, each on a distinct
native texture. Receiving a completed Mol* draw after each warm-up frame
moves all uploads into warm-up. The measured frames then record zero.
The maintained test now uses a completed draw for both warm-up and measured
frames. Its texture, coordinate and lifecycle assertions and all ten suite
inventory controls pass locally in `1068`. The
[receipt](../moving_capture_followup_receiving_20261117.json) records the
original, the controlled observation and the corrected invocation. The
same receipt verifies the original log and both ZIPs from the single
[Linux source checkpoint](https://github.com/uibcdf/molsysviewer/actions/runs/44233166206)
on `6c82a672` and `4b0b1f8a` with pandas 3.1.0. Python passes 4,756 cases
with 42 skips. All 25 notebooks and 61 core suites pass, including the
corrected atlas with zero measured uploads and all 17 interaction calculation
cases. At entry 62, `movie-composition` reaches its 180-second aggregate limit.
The hosted log has no composition phase markers before the limit, so it does
not identify a failing capture or assertion. `movie-story` is unreached.

Independent local `1070` passes measurements, the Interactions panel and ten
original/restored interaction geometries. Global memory pressure stops the
fourth suite after 14 calculation cases pass. All 36 owned processes retire
and all frozen inputs remain unchanged. The hosted run independently receives
the completed four-suite scope and preserves its own Movie failure.

An isolated composition run at 4 CPU / 3 GiB returns a renderer request
timeout during the first ZIP. The 8 CPU / 4 GiB trace passes all 16 native
720p captures in 155 seconds, with the slowest screenshot at 9.76 seconds.
The maintained guard now has progress markers and a 300-second aggregate
limit for those 16 captures, each still bounded to 15 seconds. It passes
locally without an override in 155 seconds, checking decoded ZIP/MP4 pixels,
scientific units and source indices, layout refusals and exclusion. The
receipt preserves both resource profiles, exact producer imports and original
files. The changed guard still needs complete hosted core receiving.

**Linux follow-up — 2026-11-18.** The single [source checkpoint](https://github.com/uibcdf/molsysviewer/actions/runs/44244621198)
on `ac51d77b` and `4b0b1f8a` with pandas 3.1.0 passes 4,756 Python tests
with 42 skips, all 25 notebooks and the first 38 browser entries. The calculation
entry passes its scope controls and 16 of its 17 variants. The outer runner
stops the final `water_bridge_2/default` during preparation, 1.47 seconds
after the start marker. That run reaches neither Movie entry. The
[receipt](../moving_capture_followup_receiving_20261117.json) preserves the
two original ZIPs and the native log. The earlier hosted run completes all 17
calculation variants on the same scientific source and browser version.
The revised runner gives the complete calculation entry 240 seconds. Its
scope and detector cases, scientific/scene assertions and per-operation
deadlines are retained. Local `1078` receives all 17 variants in 174 seconds
with the maintained deadline, exact fixture-worker imports and all 9,998
selected input hashes unchanged. Complete hosted receiving remains due.
Reviewing the three preserved runs also identifies
three close completed intervals between suite starts: moving capture lifecycle
233.5/240 seconds, Studio live capture 558.6/600 and Studio image export
215.8/240. These are timing observations for those runs, with their own
source inputs and overhead. Their suites retain their existing limits.

The [following Linux checkpoint](https://github.com/uibcdf/molsysviewer/actions/runs/44334625017)
on `4dc8cac5` and `4b0b1f8a` passes the 17 calculation variants within the
240-second allowance, 54 complete core entries, 4,756 Python tests with 42
skips, and all 25 notebooks. Entry 55, `movie-playback`, reports completion
at its exact final camera position, but the timer observer records one
position. The native log and both original ZIPs are verified.

The same one-position failure reproduces locally with an independent native
draw observer. The observer records the initial, interpolated and final
camera positions on the same controller. The interpolated pose first draws
1.466 seconds after arming, beyond the nominal 1.2-second sampling window.
The maintained test collects completed draws from dispatch to completion
and checks the interpolated path, exact end, stopped camera and pending-reset
settlement. It passes locally. A first-playback mutation targeting only the
final camera still fails the distinct-draw assertion. Local `1082` passes
playback, composition and the complete molecular story in one real Chromium
in 368 seconds without deadline overrides. Actual composition, story producer
and recovery imports match the frozen inputs. Pixel verification, scientific
identities, session recovery and offline playback pass. The next complete
hosted core pass remains due.

**DataCard focus recurrence — 2026-11-18.** The [next Linux run](https://github.com/uibcdf/molsysviewer/actions/runs/44356412325)
on `b6182584` and `4b0b1f8a` passes Python, 25 notebooks and 34 core entries.
After Trusted Types popup refusal, the document is focused and the current
slider is connected, but the slider has no focus and there is no requested or
published frame. The 30-second End-key assertion is the first failure. Movie
is unreached. The earlier #394 focus precondition could not protect against a
later redraw detaching the focused slider.

A real host resize in local `1085` replaces the SVG and the native slider
with the original runtime. The previously focused input disconnects, the new
input has no focus and the native structure remains zero. The correction
keeps the same native slider connected while redrawing the graph. The browser
guard now requires that identity/focus across real resize, then keeps the
one native key, concurrent layout and complete frame-publication assertions.
The first local correction reused the control after a successful card popup
round trip as well. In `1091`, Chromium emitted trusted `input` and `change`
events on the current slider, but the seek callback and Python intent were
absent. Creating the input in the opener alone still reproduced the failure
in `1094`. DataCard now reports the new document when its body moves between
windows, even at matching dimensions. The plot recreates its navigation on
that boundary and keeps it connected through redraws within the same document.
Local `1096` receives the focused resize and the source/popup native keyboard
intents, exact Python callbacks and Mol* coordinates through the popup round
trip. Its later Movie composition first ZIP export times out awaiting a
renderer capture. Isolated `1097` passes composition on the same runtime
with the 15-second per-request deadline, including native PNG/MP4 pixels and
layout refusals. The first ZIP frame takes 12.886 seconds from request to
reply. The combined failure's cause remains unknown. The same three entries
pass together in `1104` at `95d87988` with a passive renderer trace. Its first
ZIP frame takes 12.846 seconds and its actual Movie producer imports match
the frozen inputs. The [exact hosted run](https://github.com/uibcdf/molsysviewer/actions/runs/44370662706)
passes all 63 entries, 25 notebooks and 4,756 Python cases in one attempt.
It reaches the corrected DataCard path, all calculation profiles, native
Movie playback, composited media and the complete molecular story. Both
original ZIPs match GitHub's digests. This completes the current Linux
source prerequisite for deciding candidate inputs with MolSysMT.

Earlier complete three-platform source checkpoint:
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908)
on `3aff1d48` / owner-published `bc5a9297`, three Python 3.14 hosts and the
>=7.4.0 notebook profile. Linux retains all 63 core entries and 25 notebooks.
All three jobs now pass. Previous `43743095366` fails one stale
unversioned ipykernel expectation per host. The corrected four-recipe floor
guard passes 549 scoped checks; all 63 core entries and 25 notebooks now pass
in the complete source run, with original ZIPs/hash/JUnit verified.
There is one exact-head dispatch; no candidate
version/tag or installed acceptance is assigned.

| Exit | Remaining evidence |
| --- | --- |
| Complete integrated source receiving | **Current core incomplete at DataCard focus.** The corrected DataCard and all later entries, including Movie, need the same complete execution. The earlier [43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908), `3aff1d48` / `bc5a9297`, passes all three native Python 3.14 jobs, all 63 mandatory core entries in one uninterrupted run and all 25 notebooks. Six original ZIPs, hashes, native required steps and JUnit are verified. The #244/#391/#395/#397 records retain their original input scopes. |
| Exact installed artifact | After the agreed candidate preparation/authorization, identify the clean producers, versions/builds, original files/channel and hashes. Verify the packaged runtime, 5.13.1 adapters and clean installed MolSysViewer/MolSysMT pair on the required four platforms and Python 3.11–3.14. Source overlays and the previous public package do not supply this evidence. This qualification precedes and does not authorize public publication. |
| Compatibility and host closeout | Consolidate the current dependency/adapter decisions and the exact source, installed and actual-host evidence. Retain earlier 491-unit, native rendering/capture and 30-cycle results on their original inputs; review changed boundaries before reusing them for the final producer. Receive the applicable postponed visual observations or an explicit bounded disposition. Qt stays experimental; general human acceptance and the wider 1.0 programme retain their separate scope. |

The [current #244 recurrence](../archive/scientific_mirror_aggregate_budget_recurrence.md)
keeps controls and scientific mirror separate, but now gives only the latter
a 480-second aggregate allowance. Individual operation deadlines, assertions
and core inclusion are unchanged. The complete diagnostic mirror passes;
the unoverridden paired and later single-mirror attempts are resource-interrupted,
not canonical passes. The terminal hosted run receives the complete mirror boundary. Its later
Movie selector failure belongs to #395; the latest receiving also passes #397
and now requires #391's received static-bootstrap correction. Do not repeat heavy local work during
recurring shared swap.

This checklist does not reopen the architectural comparison or add v6 work.
The local cache/font/readiness/picking adapters have their recorded source
guards and remain until their separately tracked native replacements are
qualified. Waiting for another Mol* release is not a prerequisite of the
selected 5.13.1 route. Older #305/#354/#384 observations retain their actual
ownership and required exits in the wider programme; do not label them new
Mol* regressions without causal evidence. Parent #369 closes after its adopted
pre-1.0 findings and this qualification are reconciled, not when a subset passes.

Use sequential bounded executions: build/type/backend checks at 2 CPU/2 GiB,
native browser work initially at 4 CPU/4 GiB, within the agreed 8 CPU/6 GiB ceiling and
the conservative shared-memory reserve. Preserve failed native controls and
actual input hashes. Neither a skipped browser nor a postponed human check is
acceptance. Diagnose failures before repeating or broadening their gate.

The resource pilot measured busy assigned cores and spare capacity elsewhere;
subsequent browser receiving uses 8 CPU/4 GiB, with the same reserve, zero swap
allowance and own-process cleanup. This is an execution ceiling, not an
exclusive machine reservation or a claim that every operation uses eight cores.

The [three-block receipt](../molstar_closeout_three_blocks_20261115.json)
records terminal source evidence, scoped story recovery and the independently
checked package prerequisites. The current MolSysMT owner source is not the
scientific source of this CI run. Its new producer/files are not frozen; the
old 1.0.0 build-0 staging packages cannot qualify today's ChemicalStates code.

The next complete source run [43692655949](https://github.com/uibcdf/molsysviewer/actions/runs/43692655949)
on `21474b8c` is also terminal failure: Python passes 4,752 cases with 42 skips
and all 25 notebooks pass; the first nine core entries complete, then
[#397](../archive/moving_work_file_popup_readiness.md) finds a work-file
helper choosing a popup role before a positive bootstrap condition. The
unreached Movie/story assertions cannot qualify #395 in this run. Receive its
readiness correction and one new complete gate; neither source run is green.

The actual-Jupyter Movie boundary [#396](../archive/jupyter_movie_seek_pending.md) is now source-resolved by original 7.4.0 and complete current-source guard 933.
Its original failed seek, later complete notebook pass and diagnostic controls
remain distinct. Native Qt's current stopped/moving work-file receiving passes;
no historical cause or complete current-host acceptance is inferred. The
[decision packet](../molstar_closeout_decisions_20261115.md) names the remaining
staging and historical/host prerequisites.

The single new full Linux source checkpoint
[43698930436](https://github.com/uibcdf/molsysviewer/actions/runs/43698930436)
receives producer `28147339afe0315c1b252095c1442a1674fc5c9e` with the same
scientific `aee7aa65` and pandas 3.1.0. Its first GH Run Receptor observation
is pending; the complete before/after inventory confirms zero competing runs
and exactly one dispatch for this head. It retains all 63 core entries, Python
and 25 notebooks. Canonical lifecycle `903` and 536 scoped headless controls
pass before dispatch; #396's source-host resolution does not qualify final installed or other-host scope.
No installed qualification, package/tag or publication is credited.

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

## Current prolonged gate and hosted click observation

The canonical method control, plain-Jupyter reference and one-cycle pilot
pass before `809` receives **30/30** cycles in one unchanged kernel on
`a72c92ba`. The browser runs 1,662 seconds, observing ten seconds of native
playback per cycle, exact recovery and 2,248 occurrences. All six retired
native targets and their 3,720,000-byte backing buffers collect; the independent
3,983-atom witness and 47,796-byte buffer remain alive with unchanged data.
Thirty-one actual-import snapshots verify the declared scientific/addon/native
composition. Own cgroup peak is 2.55 GiB under 4 GiB; no resource stop or owned
process survivor occurs. The [receipt](../molstar_qualification_followup_20261114.json)
keeps cached development version labels, known baseline Jupyter debugger
errors and raw/page/CDP metrics explicit; it claims neither zero host growth
nor an installed artifact.

Hosted `43621650307` on that same source passes native Python (4,726 Linux /
4,695 macOS / 4,699 Windows) and all 25 notebooks. Its six original ZIPs are
size/hash verified. Complete core fails earlier this time: #388's shape
GPU/hover predicates pass, then the original click does not reach active
selection. This is distinct from #244's budget and #305/#325's original
observations. Passive diagnostics and clean local native `813` preserve the
failure as unresolved; receive the bounded hosted diagnostic before another
whole matrix. Q4/Q6 and the candidate/installed gates remain open.

## Current native picking and cell receiving — 2026-11-14

Bounded hosted diagnostic `43626475247` on `1a8d630d` passes context-menu,
controls and the complete independent scientific mirror, plus the actual full
Jupyter profile (six captures, six strong restores, four Studio captures,
eight moving cases and final lifetime controls). Its original diagnostic ZIP
is verified. The following full Linux `43627876434` passes 4,731 Python cases,
25 notebooks and fifteen complete core entries before #390's stale private
cell-reader assertion. Both original ZIPs are verified. The run stays failed;
its passing prefix is not complete core acceptance.

[Native picking readiness](../archive/native_synchronous_picking_readiness.md)
#389 has a matched original-package counterexample in two independent real
WebGL2 plugins. A narrowly source/version-gated build repair preserves the
same synchronous IDs during a pending async read; it edits no installed
provider, selection API or scientific data. Build/type, 491 JS cases and 494
scoped Python cases pass. Profile `822` receives the repaired native control
and the complete coordinate/edit/centroid/session/popup entry. That entry now
uses the [native symmetry provider](../archive/native_symmetry_receiving_provider.md)
#390 with all original lengths, angles, frames and geometry assertions intact.
Failed new-harness setups are preserved, not relabeled as product failures.

The current core inventory is 63 mandatory entries (66 including the three
remote previews). #244's [partition](../archive/controls_scientific_mirror_receiving_partition.md)
is received locally and hosted with both complete owners and original
300-second bounds. The original #388 hosted click sequence remains unobserved;
current passing diagnostics and the independent readiness counterexample do
not establish that sequence retrospectively. The next uninterrupted full
current core/source checkpoint remains required before closing the migration.
The original 30-cycle campaign keeps its prior source/runtime identity.
