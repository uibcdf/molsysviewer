---
summary: Retain transport replies across concurrent molecular ownership in Jupyter.
issue: uibcdf/molsysviewer#343
status: resolved
opened: 2026-11-08
closed: 2026-11-08
severity: medium
verification: reproduced
area: [notebook, transport, loading, tests]
guard: tests/test_inbound_edit_contention.py
normative: devguide/transport_state_ownership.md
blocked_by: []
supersedes: []
---

# Jupyter replacement begin acknowledgement

**Resolved in source:** before correction the actual kernel received the valid
begin acknowledgement, but its foreign comm thread encountered the edit lock
and raised `SystemEditPendingError`. Three real-view/threaded controls reproduce
the loss independently of the browser fixture. The correction passes 143
affected tests; a final context-preservation refinement separately passes 50
overlapping capture/concurrency controls. The unchanged canonical Jupyter guard
passes six saves and restorations; actual native Qt passes its four stopped/four
continuous cases and lifecycle/configuration controls. Expanded Jupyter v2
remains a separate failed receiving scope under #344; A5 stays partial.

## Observation

On production base `52c67a7b`, the actual kernel constructs the shared real
pentalanine scene through `apply_system_edit`, then requests playback. The
browser observes replacement `structure_data_begin` generation 5. Python remains
at `waiting_begin_ack`, with its heartbeat live and playback tracking true;
the renderer has expected/frame count 3 but no trajectory or frame changes.
The canvas is connected and visible. All observed preceding controller
operations, including `clear_all`, complete; there is no observed Viewer
runtime console error. Later socket-level observation proves that the real
acknowledgement leaves the browser with matching identifiers. An independent
widget callback receives it in Python. Three kernel `SystemEditPendingError`
events expose the dropped transport/lifecycle input; the comm remains open,
the View is not closed and 59 operations remain deferred.

The nonblocking molecular guard is correct for conflicting scene commands,
but must retain transport/lifecycle replies. Lock acquisition and registration
of a contended continuation now share the existing notification lock, preventing
an unlock/registration gap. Selected lifecycle/data-plane input returns promptly,
then resumes on the connector's existing host loop after outer ownership is
released. It re-enters the ordinary guarded handler, preserving transfer identity,
generation and closed-owner validation. Stream expiry also moves inside that
guard. No new worker, render clock, fabricated ACK or relaxed scene guard is used.
Deferred replies retain their originating connector context. Three context
controls fail before that refinement: two resumed transfers inherit the scene
owner's context and an asynchronous ownership retry inherits the releasing
thread's context. All five concurrency cases pass after explicit context
preservation; public capture signatures and digestion remain unchanged.

A real-threaded close/reply control then exposes a causal gap: scheduling scene
cleanup alone lets a late snapshot retire its broker request before the close is
processed. Endpoint-close input now cancels intentions immediately through the
existing thread-safe lifetime registries; only notifications and scene/transport
cleanup wait. That control fails before correction and passes afterward.

Actual-Jupyter receiving subsequently gets beyond reconstruction and receives
continuous primary captures, but the global entry still fails later. Attempts
07/08/09 retain respectively one/four/one completed moving cases and their
distinct remaining failures; these are not passing complete runs. Inspection
also isolates a public async-entry race with ordinary playback ownership. Four
directed controls fail before its bounded, notification-based wait is added;
another control catches cancellation between grant and consumer resumption.
The earlier 143-case selection passes, retaining 127 legacy-H5MSM warnings.
This broader capture work belongs to #319. A cancellation-at-grant control
additionally fails before its broker-cleanup correction. Final canonical
Jupyter/Qt receiving passes in 81.52/42.82 s, preserves 4,588 fixed inputs per
run, releases all 19/seven owned process identities respectively and has no
resource stop. Only Ruff whitespace and independent stdlib-import ordering
change after the final Jupyter/context run; normalized AST comparisons and
before/final hashes retain that delta. Qt receives the formatted source.
Another 460 boundary tests pass separately; counts overlap and are not added.
See the
[receiving record](../jupyter_capture_contention_receiving_20261108.json) for
separate source cohorts, unsuccessful expanded campaigns and private custody.

## Retained investigation and remaining scope

Four bounded attempts retain 4,589 unchanged selected inputs each. The fourth
operation-trace attempt fails in 108.20 s, closes all 18 owned process identities
and has no resource stop. The six preceding state/session camera-perturbation
roundtrips, including the canvas popup, pass. Raw evidence and evolving fixture
sources remain private in `A5-jupyter-moving-20261108`; they are not installed
artifact or human acceptance. The explicit frozen scientific provider is
`42f5ed3bc8f02c979b3351212554e588243de0a5`.

The actual wire/receiver observations and independent threaded regression
establish the dropped-acknowledgement mechanism. This report closes that bounded
defect. The full actual-Jupyter moving file guard remains unqualified under
[#344](../archive/jupyter_moving_capture_residual_uploads.md); its failed
campaigns are retained rather than combined into a passing result.

The complete board inventory has 100/100/100/41 records and 313 actual issues,
including closed reports. Welcome transients (#164/#247), rejected edits (#148)
and reviewed-target replacement (#306) do not establish this begin-ack stall.
A5/#319 remains partial; v2 and publications stay unadvertised/paused.
