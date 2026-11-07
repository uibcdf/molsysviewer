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

**A5 — reproduced; ambitious capture/save policy approved; Python source receiving in progress; P2.** The Viewer maintainer
session owns implementation under #315/#319 for the covering artifact and
accepted 1.0 scope. Core/Studio/native/hosted acceptance and closure remain
pending. No scientific provider algorithm needs changing. The
[source receiving receipt](../live_state_capture_receiving_20261106.json)
separates the 172 Python passes, actual Jupyter receiving and retained failures.

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
and popup rotation, then actual restoration returns that camera (four cases).
All 4,317 selected inputs remain unchanged. Popup rotation in this run is
mirrored to the primary renderer; this is **not** addressed capture from a
Studio popup. The original four stale-camera observations remain preserved.
Jupyter's `No active debugger session` page errors remain separate unresolved
environment observations; this run is not a globally error-free Jupyter claim.

The later `A5-live-capture-2` preserves four correct capture/restoration cases
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
correlated captures/restorations and the subsequent settled save pass, with
zero camera difference in that control. Before it, the primary is visible and
focused, there are no pending requests and no active structural transfer.
All 4,319 selected inputs remain unchanged. No focus-only retry was needed.
This receives the corrected primary capture path; it does not establish that
the earlier timeout had only one cause or certify hidden/background canvases.
The original failures and driver correction remain distinct evidence.

## Remaining implementation and acceptance

1. Connect Studio to the same capture/serialization owner. Send success only
   after the file is written; preserve the path and expose capture failure.
2. Bind canvas-popup requests and replies to their authenticated channel,
   including closure/reopen and panel-only Studio's canvas association. Never
   trust a payload's self-declared source. Qualify both input directions.
3. Give pending GUI saves explicit timeout/cancellation and renderer-disposal
   cleanup. No late response may write after failure/cancellation is reported.
4. Receive the native Qt host separately, including its GUI-loop behavior;
   qualify the async Python and graphical paths and retain headless saving.
5. Promote actual-renderer/Jupyter receiving to a durable registered regression,
   run the applicable combined source gate and later the consolidated hosted
   checkpoint. Preserve earlier usage-error and inventory-failure attempts.

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
