---
summary: Immediate notebook and popup saves can preserve an older cached camera.
issue: uibcdf/molsysviewer#319
status: partial
opened: 2026-11-06
closed:
severity: medium
verification: reproduced
area: [camera, persistence, notebook]
guard: tests/test_live_state_capture.py
normative:
blocked_by: []
supersedes: []
---

# Camera capture when saving notebook work

## Current hosted follow-up — 2026-11-07

**Current diagnostics:** the corrected source `e4dd58cf` receives all 44 core
browser entries, then its independent hosted Jupyter step fails without a
preserved browser phase. Source-pair Linux separately fails an updated-label
native pick, now tracked by #325; its macOS/Windows cells pass. A bounded
allow-listed summary now preserves phase/error type and counters in the safe
Jupyter command receipt without exposing raw logs. Thirteen focused cases and
the actual local Jupyter profile pass; the allow-list bypass mutation fails.
Local passing evidence does not resolve the original hosted uncertainty.

The source workflow retains its complete default. Its explicit
`receiving_scope=diagnostics` requires `source_receiving=true` and
`platform=ubuntu-latest` before acquisition or tagging. The diagnostic job has
its own name/artifact and runs only the two affected browser boundaries, with
the actual native/provider setup. It cannot qualify a candidate or complete
the Python/notebook/core matrix. The actual Bash guard matrix and workflow
checks pass 51 cases. See the [diagnostic receipt](../hosted_receiving_diagnostics_20261107.json).

Checkpoint `9a569c55` is not accepted: the completed general Linux and
three-platform Python 3.14 source-pair cells fail four pre-existing
camera-envelope assertions which omit the newly required revision field.
Their corrections retain exact dictionaries: independent HTML exports use
revision zero and an authority reset uses revision one. The affected
six-module selection passes 66 cases locally.

Core E2E `42348064230` additionally kills the expanded Studio entry at its
old 180-second outer budget. The previously completed local entry takes
198.541 seconds. A 360-second bound is now specific to that integrated entry;
individual operation deadlines, other suite defaults, caller overrides
and all assertions are preserved. Receiving through the canonical shared
browser runner passes in 193.057 seconds, with 4,478 fixed inputs and all
18 owned processes closed. No deadline override or skip was used. The separately executed actual Jupyter guard
passes in 101.551 seconds with 19 owned processes and zero cleanup survivors
or errors; it does not qualify the failed core run. Original outcomes remain
in the [hosted checkpoint](../robustness_hosted_checkpoint_20261107.json).

**A5 — partial; the bounded camera/control correction is delivered in
`ebe3d46b`; playback, hidden endpoints and consolidated acceptance
remain pending; P2.** The Viewer maintainer
session owns implementation under #315/#319 for the covering artifact and
accepted 1.0 scope. Broader hosted/installed acceptance and closure remain
pending. No scientific provider algorithm needs changing. The
[source receiving receipt](../live_state_capture_receiving_20261106.json)
separates historical and current Python selections, actual Jupyter/full Studio
receiving and retained failures. `e9def4ad` is the earlier Python/primary-renderer
checkpoint; `5148b6c5` delivers the additionally received Studio and
addressed-popup foundation. The first complete core Python run ends with 3,750 passes, five failures
and 22 skips. All five have passing scoped corrections; the complete source
repeat passes with **3,760 passed, zero failures/errors, 22 skips and 16 explicit
deselections**, in 748.66 s. All 5,401 selected files remain unchanged from the
declared early-run digest through completion. Hosted/installed acceptance and
the remaining cases below are separate.

## Earlier receiving and retained failures

**The earlier control-correction receiving was not green.** After the delivered foundation,
the before-draw control slice passes 173 Python cases, canonical JS units,
TypeScript and runtime/harness builds. The complete actual Studio entry then
exits 1: primary and popup cancellation before draw pass, but a later detached
Studio state restore retains the perturbed camera in both canvases despite
receiving the saved snapshot. All 4,660 selected inputs remain unchanged.
The cause is not yet established; a passive real-camera reset/sync diagnostic
is prepared. The earlier complete Studio pass qualifies its earlier source,
not this unresolved attempt.

The first native attempt renders with real NVIDIA WebGL2 on Wayland, then its
QTest gesture fails to rotate before any save is attempted. Teardown ends in
signal 11. The 4,339 selected inputs remain unchanged and all four tracked
process identities exit. Input delivery and shutdown causes remain uncertain;
there is no native capture acceptance. The QCore-only host preflight passes
two cases, which does not resolve WebEngine/QtAsyncio lifecycle behavior.

Later passive camera instrumentation receives all persistent save/restore and
three before-draw cases with native exit 0 and 4,663 unchanged selected inputs.
Its 881 camera observations show 17 authority poses eventually applied, with
10.5–818.6 ms delays. It does not reproduce the original detached failure and
does not replace that failed full-entry result. A controlled genuine older
camera-message experiment is prepared to test pending reset/feedback ordering.

Native attempt 2 receives four GUI/Python state/session saves, perturbed-camera
and changed-frame restoration, and cancellation before a real draw, then still
exits with signal 11 during `asyncio.Runner` cleanup. An independent actual
WebEngine probe imports no Viewer code: ordinary Qt exits 0, standard
QtAsyncio/Runner exits -11, and a single application-owned QtAsyncio loop exits
0. Each retains 4,339 unchanged selected inputs and releases all four tracked
process identities. The crash occurs when Runner re-enters Qt's application
loop for asynchronous shutdown after WebEngine teardown. These controls isolate
the local provider/lifetime seam; they do not turn the failed full native run
into acceptance. The next native receiving uses explicit application-owned
lifetime, with async cleanup while the loop is live and one final stop. No
provider patch, nested GUI pumping or worker fallback is introduced.

The application-owned native follow-up exits **0**, and its promoted durable
pytest wrapper independently exits **0** (one native case passed, one portable
collection case deselected). Four actual state/session saves through Studio
and Python preserve their exact correlated camera/frame; restoration changes
camera/frame first, then requires a matching fresh `didDraw`. Cancel unlocks
in 23.43 ms with zero draws, no file and no revival after real rendering resumes.
The GUI-thread heartbeat records 5,157 callbacks. All 4,341 declared inputs
remain unchanged; the inner four and outer five tracked process identities
exit without survivors/errors. This is local automated Wayland/NVIDIA WebGL2
evidence, not human, installed, multi-platform or globally error-free acceptance.
Eight startup errors are independently localized to Viewer #323 and now have
a separate working correction; the native pass predates those changed bytes.

The second durable native run receives the #323 caller correction with actual
Wayland/NVIDIA WebGL2: the wrapper and native child both exit **0**. Four
Studio/Python state/session saves preserve their exact correlated camera and
frame; each restore first perturbs the camera and changes the frame, then
requires the matching fresh `didDraw`. Cancel unlocks in 26.73 ms with **zero
draws**, no file and no revival after rendering resumes. The GUI-thread
heartbeat records 5,278 callbacks. All **4,341** selected inputs remain unchanged;
the inner four and outer five tracked process identities have zero survivors
and cleanup errors. Unsupported `None`/`get_form` stderr observations fall from
eight to **zero**, without suppression. One GBM fallback and one D-Bus address
diagnostic remain retained; this is not a globally error-free Qt claim.

The third genuine older-camera probe subsequently exits **1**, with all
**4,666** selected inputs unchanged. Its original held `MessageEvent` is
delivered exactly once through the actual registered listener. With real Mol*
drawing paused using `noDraw`, the first resumed draw shows the older camera
instead of the saved authority pose. This establishes a stale-camera ordering
regression in that controlled case. It does **not** establish that this is the
exact temporal cause of the earlier canonical detached-Studio failure. The
failed, inconclusive and passive attempts remain separate historical evidence.

The next working correction stamps authoritative camera revisions, records
camera intent before deferred scene application and rejects older camera
feedback for that intent. The public camera API retains partial snapshots and
non-unit `up` vectors. Six direct Python cases and the overlapping 87-case
combined selection pass. Frontend source is prepared, but its current build,
canonical units and complete Studio receiving are **in progress**, not passing
evidence. The prior native and browser passes qualify their recorded inputs;
they do not qualify these newly changed bytes. A5 remains partial.

## Final resumed receiving of this source slice — 2026-11-07

After the maintainer resumed execution, the complete canonical Studio entry
passes with **native exit 0 in 198.54 s**. All 4,011 selected inputs remain
unchanged, all 17 owned process identities close, and there is no opt-out.
Actual primary, canvas-popup and detached-Studio state/session restores,
genuine old-message rejection, new physical input, partial/non-unit-up
snapshots, later reset/focus and cancellation before drawing all pass. The
navigation cases pause both real renderers and require the originating canvas
to complete and relay its camera before the primary resumes; intentional peer
echo suppression is preserved. Releasing the test's message instrumentation
also preserves production listeners for the following actual Cancel workflow.

The fourth native Qt run is now accepted by the ordinary approval route and
passes with **native exit 0 in 32.34 s**, all 4,341 selected inputs unchanged and
zero process survivors. Its four saved files independently match their exact
correlated camera/frame; all restores perturb the camera and frame first and
require a matching fresh draw. Cancel unlocks in 39.95 ms with zero draws,
without a file or revival. Unsupported-None and deprecation stderr counts are
zero; one GBM fallback and one D-Bus diagnostic remain retained. This is actual
local Wayland/NVIDIA WebGL2 receiving, not human or installed qualification.

The bounded source correction is delivered in `ebe3d46b`. A5 remains
partial for continuous playback, hidden endpoints and applicable consolidated
hosted/installed and postponed human acceptance. The interrupted Studio3 is
operator cancellation, not a passing run or a newly diagnosed product defect;
the earlier rejected Qt launch produced no process and remains historical.

## Observation and duplicate review

An actual isolated JupyterLab/ipykernel/anywidget session renders bundled
dialanine through real Mol*/Chromium. Ordinary mouse rotation precedes calls
to public Python save methods in that live kernel. Both notebook and canvas
popup supply independent observed cases; the files themselves are inspected.

| Origin | Public method | Saved equals pre-save Python cache | Difference from displayed camera components |
| --- | --- | --- | --- |
| Notebook | `save_state` | Yes | 10.27 maximum absolute component difference |
| Notebook | `save_session` | Yes | 15.49 |
| Canvas popup | `save_state` | Yes | 4.54 |
| Canvas popup | `save_session` | Yes | 9.37 |

The component metric compares position, target and up vectors; it is not a
molecular displacement or a scientific interaction measurement. In both
session cases, the displayed camera before and after saving is identical, so
ongoing movement alone cannot explain the mismatch. After actual cache/display
convergence, the control session has zero difference. Coordinates remain
exactly unchanged on every save.

The source is `a7f1c1c73e1b35e734160a994c059032e1658d8d`, controlled MolSysMT
`e119953435a25c72e9a65b7428f74b1c2430b4f1` and PyUnitWizard
`02d0015fa7d3149d92c0e632b8e584f6a47c37dc`, Python 3.14.7. All 4,312 selected
source/runtime/provider/driver inputs remain unchanged. Private evidence is
`A5-camera-probe-2`, with its command receipt, observations, actual files and
driver sources. The first attempt's Chrome launch failed before any page
because the test TMPDIR exceeded the Unix-socket path limit; a short managed
temporary directory corrects the driver. Existing Jupyter debugger page errors
are retained separately, not attributed to Viewer. This is observational
reproduction, not yet a fixed-code or actual restore qualification.

The complete duplicate inventory has four pages / 317 records. Closed #38/#68
define and document persistence; #224 receives Studio file operations; #234
receives camera mirroring; #36 receives native Qt camera replies. None protects
the immediate live-notebook capture seen here.

## Diagnosis and accepted direction

`save_state` requests a camera and synchronously waits, pumping only the native
Qt event hook when present. `save_session` directly uses `export_state`.
Notebook camera pushes are debounced by 300 ms. Request/reply ordering and
actual Studio/restore paths still need passive receiving; source inspection
alone does not establish every timing mechanism.

Keep existing Python save calls synchronous and atomic: returning means the
file has been written or an error raised. Preserve headless scene saving and
cached inspection through `view.camera.get_snapshot()`. Do not introduce hidden
background saves or re-enter a busy notebook kernel unsafely. Studio should
include an acknowledged resolved camera from the initiating canvas in its save
intent, with the normal validation and persistence owner still authoritative.

The principal maintainer explicitly chose the more ambitious, user-useful
alternatives in the 2026-11-06 session, accepting the implementation cost. This
approves coherent live capture and save, not merely a shorter camera debounce.
The implementation keeps the existing synchronous methods and adds explicit
awaitable saves; Studio retains one Save action and will capture automatically.
It does not adopt F1's wider immutable public scene API or change publication
authority.

| Alternative | Advantages | Limitations / disposition |
| --- | --- | --- |
| Push cameras more often | Low latency; no extra user API | Cannot guarantee freshness while a notebook kernel is busy; complementary only |
| Explicit capture, followed by an ordinary save | Composable; preserves synchronous/headless methods | Re-reading a mutable cache between the two operations can save another camera; a correct design must pass the exact captured scene to the writer |
| Capture and save in one awaitable operation | One user action; exact captured payload; explicit errors; same writer as synchronous saving | Requires correlation, scene/frame validation, cancellation/lifetime handling and GUI/native receiving; accepted direction |

The first source implementation adds `view.save_state_async(path, *,
timeout=5.0, skip_digestion=False)` and `view.save_session_async(...)`.
`timeout` is in seconds and bounds renderer capture, not filesystem I/O.
These methods yield while waiting for the primary renderer, then serialize on
the owning thread with the existing atomic writers. They do not start hidden
background writes or claim fully asynchronous H5MSM computation/I/O. Existing
`save_state`/`save_session` remain usable without a live frontend; the former's
camera refresh is explicitly best-effort. `camera.get_snapshot()` remains a
cached read. No public `camera.capture_snapshot()` has been added.

## Infrastructure and invariants

The private pending-request owner gives each request a unique identifier,
source endpoint, expected reply event, scene token and deadline. It bounds
pending entries, detaches accepted data and rejects unrelated/duplicate/late
replies. Cancellation, endpoint retirement and View closure release owned
requests. The connector must validate endpoint ownership before routing replies;
the first integrated path addresses the primary renderer only.

An explicit capture follows structural delivery and the widget's existing
scene queue, waits for a completed Mol* draw, and samples camera and frame in
one JavaScript turn. Python keeps a detached scene and checks it again before
writing. Passive camera telemetry cannot replace this payload. A changed
scene/system/frame, invalid camera or missing/refusing renderer produces an
error and preserves the destination. The trajectory is not copied to wait for
a reply. Arbitrary raw-array edits keep their existing explicit-sync contract.

The async ArgDigest adapter preserves coroutine identity and digests at entry,
without holding the molecular edit lock across a kernel yield. Final capture
validation and writing reacquire the owner lock. SMonitor spans the awaited
operation; capture failures use a catalog-backed error.

Initial source receiving covers 22 protocol/lifetime cases and then 120 combined
Python API/state/session/lifecycle guards. The actual
isolated Jupyter run `A5-live-capture-1` completes with native exit 0 in 36.06 s:
both formats save the exact passively observed correlated reply after notebook
and popup rotation, then invoke restoration and observe camera convergence
(four cases; the stronger acceptance qualification below applies).
All 4,317 selected inputs remain unchanged. Popup rotation in this run is
mirrored to the primary renderer; this is **not** addressed capture from a
Studio popup. The original four stale-camera observations remain preserved.
Jupyter's `No active debugger session` page errors remain separate unresolved
environment observations; this run is not a globally error-free Jupyter claim.

The later `A5-live-capture-2` preserves four exact captures and restoration invocations
but exits 1 on an additional settled save after popup closure (capture timeout).
Its 4,317 selected inputs also remain unchanged. This is not a passing final
run. Passive diagnostic `A5-live-diagnostic-1` additionally exposes a real
lock-publication race: a capture reply can resume the awaiting kernel task
before the frontend handler releases the molecular edit lock. Its follow-up
status probe also has a driver-only missing argument, retained separately.
The race is reproduced causally by the new lock-notification test: it fails
with `still_locked` before the correction, then the 23-case protocol/lifetime
module passes after replies are published outside that lock and the request
registry is made thread-safe. Future callbacks also run outside the registry
lock. Neither original failure is hidden by the earlier successes.

`A5-live-diagnostic-2` then completes with native exit 0 in 39.71 s: four exact
correlated captures, restoration invocations and the subsequent settled save pass, with
zero camera difference in that control. Before it, the primary is visible and
focused, there are no pending requests and no active structural transfer.
All 4,319 selected inputs remain unchanged. No focus-only retry was needed.
This receives the corrected primary capture path; it does not establish that
the earlier timeout had only one cause or certify hidden/background canvases.
The original failures and driver correction remain distinct evidence.

### Receiving refinement and Studio integration in progress

Review of those retained drivers finds that their restore calls began with the
camera already at the saved vantage point. They prove exact captured bytes,
restoration invocation and convergence, but **do not independently prove camera
restoration from a different view**. This qualification supersedes earlier
"restored vantage" claims in the summary receipt; original evidence remains
unchanged. New durable browser/Jupyter guards perturb the camera first and
require recovery; the Jupyter guard additionally observes a fresh completed
Mol* draw. They are not passing evidence until their actual runs complete.

The working source now gives Studio one deferred Save intention using the same
detached capture and atomic writers as Python. Its result follows actual bytes;
the initiating panel and associated canvas retain authenticated, separate
identities. Capture has a ten-second host-loop deadline and a cancel action
before writing. Closure, timeout and cancellation release owned requests and
cannot be followed by a late write. These are working-source changes, not a
closed/installed qualification.

An actual isolated Jupyter Studio probe first reproduces
`scheduler_unavailable`: kernel comm dispatch runs on another thread than widget
creation. The corrected scheduler binds the actual kernel/asyncio host and
marshals timer arming/cancellation onto that host; it does not let an unrelated
worker appoint another loop. The follow-up probe exits 0 in 29.60 s, writes the
actual scene, drains both pending registries and preserves all 3,912 selected
inputs. Qt keeps its own GUI-thread QTimer path. Its scheduler tests are not
visible-window Qt acceptance.

The real widget/browser Studio receiving then exposes missing panel metadata
in the canvas-popup bootstrap: the molecular scene exists, but session saving
and restoration remain disabled. Canvas popups now use the same complete live
projection as embedded canvases, including authoritative panel summaries and
without duplicate operations or addon widget replay. The four-case regression
fails before this correction; all 30 popup projection/fidelity tests then pass.
The browser rerun remains pending at this checkpoint.

Independent review also identifies primary-result fanout, error diagnostics
losing their owner, and verdicts held behind another canvas's structural stream.
These control replies are being made owner-specific and independent of that
stream. Completion publication now waits for the outer molecular guard to
release, including cancellation, lazy expiration and public close; the 46-case
capture/deadline gate passes. These scoped results overlap other Python counts
and do not constitute consolidated hosted, installed or complete A5 acceptance.

The combined Python selection now passes **245/245** in 57.23 s; a separate
**428-case** reporting/release/distribution/workflow selection passes. The
inventory caught the new owned `widget.close` override without digestion:
its public wrapper now declares `skip_digestion`, with an internal finalizer
that does not import digesters during Python shutdown. The reviewed inventory
is 741 reachable callables, all digested and without exemptions. The failing
223-pass/three-failure attempt and a command-only wrong-filename attempt are
retained separately.

The durable actual-Jupyter follow-up exits 0 in 98.22 s: **six** saves and
restorations from a perturbed camera, each followed by a fresh completed draw
(two Python, four Studio across notebook/canvas-popup and both formats).
Actual held replies also demonstrate GUI cancellation and autonomous timeout
without late writes. Both registries/timers drain; cleanup reports 18 tracked
process identities, zero survivors/errors and removed ephemeral credentials.
The 4,328-file selection has one difference: an unexecuted release-gate test
was edited during the run. Product/runtime, providers and executed drivers
remain unchanged; this is not an all-inputs-immutable claim. Eleven host debugger
diagnostics remain retained, including the plain-kernel baseline.

The persistent-widget browser guard has stronger scene/frame input and has not
yet passed its whole entry. Primary and popup state roundtrips, late-cancel
rejection and causal same-ID isolation pass. A popup session restore now
acknowledges its correct owner but fails a subsequent camera/frame convergence
assertion. Retain that failure and inspect actual renderer state before another
product edit. The separate live-Jupyter pass cannot override this narrower
unresolved observation. Detached, native Qt, playback and combined hosted
acceptance remain open. The subsequent per-endpoint correction and receiving
below supersede that pending structural-restore diagnosis.

The diagnostic records popup array-load completion followed by a late
`clear_all` from the primary's browser-side fanout. The popup had acknowledged
the structure; the later clear removed it. Scene/runtime projections now use
each endpoint's own queue, including explicitly addressed primary JSON fallback,
and the widget relays addressed domain commands before primary application can
delay them. The final **101-case** transport/Studio/endpoint selection passes.
The complete Studio browser entry then exits **0**, with all **4,658** selected
inputs unchanged: original PNG/HTML/UI/disposal assertions and six persistent
primary/popup/detached Studio state/session camera-perturbation roundtrips,
same-ID isolation, batch ownership and late-cancel rejection.

The actual-Jupyter guard is repeated for those new transport bytes: native exit
**0**, 96.65 s, the same six camera-perturbation/fresh-draw roundtrips and
cancel/timeout no-write controls, with all **4,328** selected inputs unchanged.
All 17 tracked process identities are released; credentials are removed.
These guards compare saved/displayed structure indices; a new deliberate
pre-restore structure-index change remains useful acceptance for the combined
camera/frame boundary. No broader camera-projection, native Qt or continuous
playback claim follows from these results.

## Remaining implementation and acceptance

| Boundary | Current source receiving | Remaining acceptance |
| --- | --- | --- |
| Shared Studio capture/writer and truthful success | Python/actual Jupyter/full Studio entry pass; path, overwrite, actual bytes and captured camera are checked | Consolidated source/hosted/installed receiving for the intended artifact |
| Authenticated popup/panel association | Primary, canvas popup and detached Studio both-format roundtrips, changed-frame restores, same-ID ownership and per-endpoint structural order pass | Hidden/background receiving and additional endpoint-lifetime combinations |
| GUI deadline/cancel/disposal | Host-loop and owner tests, actual Jupyter timeout, full Studio and final native before-draw cancellation pass without late writes | Consolidated host/platform acceptance |
| Native Qt | Fourth durable actual GUI-loop run receives the final camera/control runtime: four format/origin cases, perturbed camera/changed frame/fresh draw, heartbeat, before-draw cancel and application-owned clean shutdown pass; zero unsupported-None errors | Other bindings/platforms, consolidated qualification and postponed human observations remain separate |
| Durable regressions | Existing registered Studio browser entry plus opt-in local Jupyter profile and explicit strict-release/hosted core CLI route; complete core repeat passes 3,760 cases/22 documented skips | Consolidated hosted and exact-installed gates remain pending |

### Historical before-draw regression and received control correction

A private real-renderer probe now reproduces the control-queue problem with
drawing suspended through Mol*'s actual animation loop API. In both primary and
popup Studio, Python accepts cancellation while no camera snapshot or draw has
occurred. The requesting window has already received the terminal messages,
but its controls remain disabled at "Cancelling" through subsequent DOM frames.
Resuming the same render loop immediately applies the queued verdict and
unlocks the controls. The backend registries drain, no file exists before or
after the late real reply, and natural ten-second timeout cases unlock normally.
The probe deliberately exits **1** for this confirmed regression, with 4,656
unchanged selected inputs, no page errors and complete owned-resource cleanup.

The next correction needs authenticated terminal control outside scene queues
and an abortable draw wait, correlated by the actual broker request and revision
(not the separate Studio request ID). Register abort ownership before queuing
the draw barrier; dispose subscriptions/timers and prevent a late response from
reviving the capture. Keep the backend deadline authoritative and retain the
existing render clock; no GUI-only watchdog or hidden canvas switch is approved.

The Python part of that correction was then received in working source. Abandoned
broker reservations notify only their exact renderer/request/revision, after
molecular ownership is released; successful captures do not send an abort.
The endpoint registry removes an exact unsent barrier before the control is
transmitted, preserving other captures and scene operations. A transport
failure cannot leave the abandoned Future pending. Eight initial causal cases
fail before the change; the expanded six-module capture/Studio/deadline/runtime
and transport selection passes **141/141** in 22.95 s. These are protocol/file
guards, not acceptance of the new browser or native Qt control route. That
receiving was pending at this checkpoint; the later native results above and
their own recorded inputs retain their separate scope.

### Remaining moving-structure and hidden-endpoint receiving

For playback, frame/camera and all frame-dependent projections must describe
the same completed draw. Rewriting only a saved structure index is insufficient:
for example, NPT box geometry is materialized under shapes. Build a detached
captured recipe and validate stable scene/system/analysis revisions without
navigating or pausing the live View. The private Qt primitive probe confirms
QtAsyncio viability on this environment, but does not replace actual
WebEngine/capture/file receiving; ordinary asyncio alone does not dispatch Qt.

Continuous playback needs a deliberate receiving case: the current first
implementation refuses a scene/frame change during capture rather than mixing
versions. Any later support for a moving timeline must preserve a coherent
captured frame without introducing a second playback clock or silently
stopping the user's work. This remains part of the accepted A5 implementation,
not a newly declared post-1.0 deferral.

## Required receiving

Receive both actual save formats and their restored vantage points through
notebook and canvas-popup input, plus Studio save intents. Correlate replies;
reject stale/delayed or wrong-owner responses. Retain headless saving, native
Qt behavior and exact molecular data. Verify timeout/cancellation/disconnect
cleanup and no late writes or scene mutation after refusal. Review other users
of the same camera helper without inferring failures not observed there.

The direction is approved; remaining implementation and receiving are open. Commits carry
`[skip ci]`; consolidated hosted and installed qualification stay separate.
Human/visible-host receiving, tags, packages and both 1.0 publications remain
paused. A5 is not a received progress item.
