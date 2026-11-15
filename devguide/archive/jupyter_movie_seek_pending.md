---
summary: Receive notebook Movie on the corrected ipykernel comm transport.
issue: uibcdf/molsysviewer#396
status: resolved
opened: 2026-11-15
closed: 2026-11-15
severity: high
verification: reproduced
area: [movie, jupyter, concurrency, receiving]
guard: tests/test_movie_studio.py::test_live_jupyter_movie_authoring
normative:
blocked_by: []
supersedes: []
---

# Correlated Movie seek in an actual notebook

**Resolved in source — 2026-11-15.**

## Resolution

The corrected supported notebook host uses `ipykernel>=7.4.0`, whose native
shell transport includes upstream #1529. Independent kernel-only control 913
and actual server/kernel observations 910/912 identify the pre-handler
notification-loss mechanism; no Movie calculation was running during that
observed interval. Original failures and their timelines remain preserved.

The original-provider 7.4.0 controls and earlier complete guard 916 are now
complemented by **current-source actual-Jupyter receiving 933**. The maintained
`guard` passes one test with zero failures/errors/skips in 108.92 seconds.
It executes ten Python-edit/kept-draft/seek cycles in one kernel and all eight
Movie phases: both popups, Python/Studio pause, native media, independent
session recovery and close/cancel/late-reply protection. Scientific coordinates
and source identity remain unchanged. There are no Python/server/scheduling
delegates or altered operation deadlines.

Actual loaded kernel provenance confirms original isolated ipykernel 7.4.0.
The consumed scientific source is Git-verified MolSysMT `bc5a9297`, with its
unchanged recorded `4ffb82e4` native backend; MolSysViewer source base is
`df9f898c770347719bac02d2e240050f9d620af1`. The
[receipt](../molstar_closeout_three_blocks_20261115.json) records actual imports,
57 provider-file verification, original archive SHA, native media and private
custody. All 9,983 selected inputs remain unchanged, all 20 owned processes
retire and no resource stop occurs. Peak summed own RSS is 3,246 MiB under
8 CPU/4 GiB; supervisor duration is 112.61 seconds.

The complete source checkpoint 43748320908 also passes three Python 3.14
hosts, all 63 core entries and 25 notebooks. This closes the reproduced
source-host comm defect. Shared legacy-prefix adoption stays with MolSysSuite
#200, and clean installed/final-candidate, other-host and human qualification
remain separate. No shared environment, upstream source or Movie algorithm
is changed in this archival step.

## Earlier investigation and receiving history


**Source correction received — 2026-11-15:** the interleaved comm/execute stall
is reproduced without MolSysViewer on ipykernel 7.3.0. Original 7.4.0 provider
bytes pass the minimal 30-cycle control and the complete selected Movie pytest,
now requiring ten edit/seek cycles before its existing popup/media/recovery
suffix. Component notebook recipes require `ipykernel>=7.4.0`; the legacy
shared-prefix transition belongs to [MolSysSuite #200](https://github.com/uibcdf/molsyssuite/issues/200)
and remains paused. Complete current source/installed receiving is separate.
This does not explain the earlier #615 first-canvas timeout.

The three-platform source checkpoint `43743095366` preserves one failing
environment-contract assertion per host: its older literal `ipykernel`
expectation rejects the corrected versioned recipe. The test now requires
`ipykernel>=7.4.0` and separately protects that floor in all four maintained
notebook recipes. All 549 selected source-workflow/reporting/link checks pass
in `921`; source CI must still receive the corrected input. This is a test
expectation correction, not an additional runtime or transport change.

The current source receives native Qt's stopped/moving work-file flow in
`888`, but the separate actual-Jupyter Movie guard fails in `889` on
MolSysViewer `21474b8c`, scientific source `aee7aa65` and the reviewed 5.13.1
runtime. The unchanged workflow authors three tracks, receives Python's
duration edit and retains the draft, then enters Preview and requests 0.4 s.
Its idle predicate times out at the unchanged 30-second bound. Only two of
the eight Movie phases have completed; export/recovery and the popups are
unreached in this attempt.

The preserved pre-retirement browser observation shows the correlated
`movie_seek` pending ID, editor revision 6, `busy=null` and native frame 0.
The trajectory, annotation and capture-safety predicates are healthy. The
recipe has already accepted a frame-two key at 0.25 s; no applied transition
or new correlated result is observed. A bounded post-failure kernel request
also times out. Idle thread stacks do not identify the lost boundary or
establish a deadlock. Jupyter's separately observed `No active debugger
session` messages do not establish causality either.

All 9,979 selected inputs remain unchanged, all 20 owned processes retire,
peak summed RSS is 2,702.6 MiB under 8 CPU/4 GiB, and no resource stop occurs.
Keep this failed actual-host result separate from source/browser prefixes,
Qt, installed packages and human acceptance.

The complete four-page history contains 394 entries and 366 non-PR issues.
#365's earlier proven scene admission, #366's cross-loop completion and
#383's field label are related; current evidence does not assign this
observation to those resolved causes. #395's adapted story selector is a
different receiving boundary.

## Investigation and acceptance

Trace actual browser send, kernel comm entry, scene admission, host callback,
Movie operation/request, native apply/reply and correlated result. A passive
diagnostic may delegate each real handler once without changing messages,
state, timers, user actions, assertions or deadlines. It is not a substitute
for the uninstrumented complete guard or causal regression.

If a concrete defect is established, preserve a failing causal control and
receive its correction. Run the existing selected pytest guard with
`MOLSYSVIEWER_JUPYTER_TEST=1`, retaining all eight phases, both popup owners,
Python/Studio pause, native draw, archive/session and late-reply/close checks.
No blind click retry, forced state, substituted bridge or extended deadline
qualifies this boundary. The [three-block receipt](../molstar_closeout_three_blocks_20261115.json)
owns consolidated evidence and private-custody references.

## Diagnostic receiving

`890` reproduces the pending seek with passive delegation of the real event,
callback and Movie owners. It records event admission, callback execution on
the connector loop and operation entry; it does not yet establish the cause.
All selected inputs remain unchanged and all owned processes retire.

`891` and `892` receive all eight phases with an out-of-band task observer;
`893` adds comparable browser/Python clocks, and `894` removes that observer
thread again. Those four complete diagnostic workflows pass with unchanged
scientific/scene assertions and deadlines. Their task samples contain an
already completed seek rather than a suspended counterexample. Neither those
passes nor the absence of scene contention in their traces fixes the earlier
failure or proves that the observer explains it.

The maintained receiver now records bounded send/receive epoch and monotonic
times, action/request correlation and kernel connection/status at failure.
These are passive diagnostics, without a changed command, retry, substituted
reply or product deadline. Receive the original complete uninstrumented guard
on these changed receiving inputs; retain the intermittent failure and cause
uncertainty even if that attempt passes.

The original uninstrumented selected pytest guard then passes all eight phases
in `895` (79.15 s pytest, 83.77 s supervised). It uses the new bounded browser
failure diagnostics but no Python delegates, extra observer thread or timer.
All 9,979 selected inputs stay unchanged; all 20 owned processes retire, with
no resource stop. This receives the current complete workflow once. The
original `889`/`890` failures and their unclassified intermittency remain
open; later success is not a causal correction. No further identical heavy
retry is justified without a new discriminating observation or changed input.

Source inspection also shows that Movie's pending UI action clears on its own
correlated result or an immediate send exception. A later state summary alone
does not acknowledge that action. Any recovery design must retain request/job
ownership, distinguish an unknown outcome from failure, and avoid repeating an
export or accepting a late reply as completion of a different command. This
observation is a recovery constraint, not a diagnosis of the missing original
completion or permission to hide it behind a timer.

## Discriminating transport observation

Control `910` reproduces the same failure with comparable browser/Python epoch
clocks, bounded wire-versus-processed-IOPub header observations and a read-only
pending-task observer. The browser records sending the correlated `movie_seek`
at `1794762213767` ms; the Python comm handler first admits that same request
at approximately `1794762249312` ms, about 35.5 seconds later. The browser's
pre-retirement snapshot is earlier, at `1794762243782` ms: kernel connection
is connected, status is idle, editor revision is six, native frame is zero
and the action is still pending. No correlated Python seek operation or
renderer request has been observed during that UI wait. The two preceding
Movie authoring/edit phases pass; later phases remain unreached.

This localizes the measured delay before Python's application-level handler;
Jupyter's `anyMessage` send signal alone does not prove actual socket delivery
or a server-to-kernel send. Browser-native WebSocket frame times and the real
server incoming/ZMQ-send boundaries are the next discriminating observations.
They must delegate once and retain bounded metadata, not message bodies,
tokens or scientific payloads. Do not assign a browser/server/kernel cause
until those stages are observed. The earlier failures retain their original
unknown scope. All 9,979 selected inputs stay unchanged and all 19 owned
processes retire; the supervisor records no resource stop.

Control `911` adds actual server incoming/ZMQ-send and browser-native WebSocket
frame observations; the full eight-phase workflow passes, so it does not
explain the failing attempt. Control `912` then repeats the critical
Python-edit/kept-draft/seek sequence ten times in one kernel before the same
suffix. Six cycles pass. The next seek reaches the server and ZMQ send in
approximately 1–2 ms, but Python admits the correlated request about 35.7
seconds later. Neither browser-side queuing nor an already-running Movie
calculation accounts for that observed pre-handler interval. Original handler,
server, wire and pre-retirement observations remain in private custody.

## Existing upstream correction and bounded adoption

Minimal control `913` uses only a real ipykernel and jupyter_client comm target,
without MolSysViewer, widgets, browser, server or science. A cell publishes a
comm and the client answers during and after execution. Thirteen cycles pass
with ipykernel 7.3.0; the next two messages do not reach the callback within the
diagnostic five-second admission bound. The application's 30-second deadline
has not changed. This native result, together with `912`, distinguishes the
provider transport boundary from molecular scene execution.

The existing [upstream correction](https://github.com/ipython/ipykernel/pull/1529)
is included in public 7.4.0. The inspected 7.3.0 shell reply bypasses its
ZMQStream with a raw socket send; 7.4.0 sends through the owning stream, avoiding
the documented lost read-edge mechanism. No upstream patch is copied into
MolSysViewer, and no new external issue is published for an already fixed bug.

Control `914` verifies all 57 selected package files from original conda-forge
`ipykernel-7.4.0-pyh4a3486f_0.conda` (SHA-256
`9ea2c55f4a9aa9146f614f827412716c6f53cd08eace21297b687301b804bb97`)
and passes 30/30 native comm cycles through an isolated provider path. `915`
passes the ten-cycle real Movie diagnostic and all eight original phases.
The maintained guard now keeps those ten native edit/seeks and asserts their
completed count. Kernel-origin evidence records the actual loaded version/path.

The uninstrumented selected pytest then passes in `916`: 1 passed in 95.76 s,
ten edit/seeks, eight Movie phases, both popup owners, Python/Studio pause,
native media, independent session recovery and close/late-reply protection.
There are no Python delegates, observer threads or modified server in this
receiving. Original provider bytes match before/after; all 9,979 selected inputs
stay unchanged, all 20 owned processes retire and no resource stop occurs.
This receives the source solution on that notebook-host profile, not a clean
solver-installed candidate, other platform, native Qt or human acceptance.

The maintained notebook recipes and installation/developer instructions now
require ipykernel >=7.4.0. This is a host requirement; headless/Qt runtime
dependencies remain unchanged. The shared legacy prefix still has 7.3.0 and
was not modified. MolSysSuite #200 owns its controlled migration/adoption and
other-consumer review. Keep that pending ownership visible, and keep the
historical #615 uncertainty separate from this reproduced comm-transport fault.
