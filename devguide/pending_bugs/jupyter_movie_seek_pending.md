---
summary: Actual Jupyter Movie seek remains pending after authoring and Python editing.
issue: uibcdf/molsysviewer#396
status: active
opened: 2026-11-15
closed:
severity: high
verification: measured
area: [movie, jupyter, concurrency, receiving]
guard: tests/test_movie_studio.py::test_live_jupyter_movie_authoring
normative:
blocked_by: []
supersedes: []
---

# Correlated Movie seek in an actual notebook

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
