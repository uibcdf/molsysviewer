# Transport and popup audit follow-ups

**Status:** audit record. Its execution order is superseded by
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md).

This document records the additional work found after R2, D3, D4, the Qt
real-window validation, and Contracts S8/S9 had landed. It complements
[`open_items_after_the_2026_08_smoke_round.md`](open_items_after_the_2026_08_smoke_round.md);
it does not replace that broader smoke-test backlog.

**Completeness rule:** the actionable audit inventory is the union of these two
documents. This file is intentionally not a second copy of the nineteen smoke
items, but the delegated items are indexed below so that reading this file alone
cannot hide them.

The audit inspected the current `main` implementation and ran the focused
Python contract set for popup snapshots, stream timeout/ordering, Qt transport,
and wire serialization with 12 workers: **46 passed**. The complete Python,
JavaScript, TypeScript and browser totals reported by the preceding development
round were not re-run as part of this audit.

## Executive decision

R2, D3, D4, S8 and S9 are architecturally sound and remain closed. The work
below is not a request to redesign them. This audit adds one concrete D4 defect
to the active defects found by the smoke inventory, two lifecycle
guarantees to prove or sharpen, documentation drift to remove, and one measured
pre-1.0 performance improvement to implement.

## P0 — Correctness defect

### 1. Address fallback cancellation to the popup endpoint

**Observed defect.** A popup-targeted binary stream retains its
`target_endpoint_id`. On failure, `_fallback_binary_structure_stream` adds that
target to the JSON fallback, but sends the preceding `structure_data_cancel`
without it. The widget host therefore consumes the cancel locally instead of
relaying it to the popup. The popup can retain a partial array-native generation
while receiving the replacement JSON generation.

The sibling `_cancel_binary_structure_stream` path already propagates the
target, so the two cancellation paths disagree.

**Required change.** Include the original `target_endpoint_id` on the fallback
cancel whenever the failed stream was endpoint-targeted. Keep host streams
untargeted.

**Required tests.**

- Start a canvas-popup-targeted stream, force connector failure or ack timeout,
  and assert that both `structure_data_cancel` and `load_molsys_payload` carry
  the same popup endpoint.
- Assert that an embedded-host stream still emits both messages without a
  target.
- At the browser seam, assert that the popup receives the cancel before the
  targeted JSON fallback and releases the partial generation.
- Mutation check: remove the target from the cancel; the regression test must
  fail.

## P1 — Guarantees that still need evidence

### 2. Test widget reconstruction and kernel-session replacement end to end

The router correctly rejects stale `session_id` values in Python and
TypeScript. That proves message validation, not the complete lifecycle promised
by R2: an old popup must close or become visibly disconnected after widget or
kernel replacement, and a replacement popup must authenticate with the new
session and bootstrap from a fresh canonical snapshot.

Add a browser lifecycle test covering:

1. open and authenticate a popup;
2. replace the host model with a new `runtime_session_id`;
3. prove that the old popup cannot send an accepted command or consume a new
   projection;
4. open a replacement popup and prove that it receives the current snapshot;
5. prove that no state or pending request leaks across sessions.

Mutation check: allow the old session to remain attached; the test must fail.

### 3. State the D3 timeout semantics precisely and evaluate event-loop expiry

The 30-second stream deadline is **cooperative**. It is checked when the kernel
next enters a relevant main-thread path. This is a deliberate safety choice:
`widget.send` must not be called from a timer thread. It also means an idle
kernel can retain stream arrays beyond 30 wall-clock seconds.

Two actions are required:

- Document the current guarantee as "released on the first relevant kernel
  entry after the deadline", not as unconditional release at 30 seconds.
- Investigate scheduling the check on the owning Jupyter/Tornado/asyncio event
  loop. Adopt it only if the callback is demonstrably executed on the widget's
  safe thread and works across the supported notebook hosts. Do not introduce a
  background thread merely to make the timeout look strict.

If event-loop scheduling is not portable, keep the cooperative model and add a
test that advances the clock while idle, then triggers one entry point and
proves deterministic release and fallback.

### 4. Add seam-level tests when behavior depends on composition

The smoke round found seven failures that were invisible to large unit suites:
JSON-incompatible NumPy scalars, unit stripping, scene-before-structure,
half-built-scene camera bounds, panel-only visibility assumptions, and stale
Mol* representation refs. These were failures between individually tested
pieces.

For future transport or rendering changes, require at least one test through
the complete relevant seam:

- Python message creation -> connector serialization -> browser reception;
- structure generation -> S8 barrier -> scene projection;
- popup request -> canonical snapshot -> authenticated endpoint;
- Mol* state mutation -> rendered state or state-tree assertion.

This does not replace unit tests. It prevents them from being the only evidence
for behavior whose correctness depends on timing, serialization, or Mol* real
state.

## P1 — Documentation accuracy

### 5. Reconcile the retained R2/D3/D4 design records with the shipped state

The retained design records correctly explain why the architecture exists, but
several sections still describe closed work as pending:

- `data_plane_architecture.md` says at the top that D0-D4 and Qt binary are
  complete, then later says Qt still uses JSON and lists R2, D3 and D4 as the
  remaining execution order.
- `runtime_message_router.md` still presents `PopupReplayLog` and a current JSON
  canvas bootstrap as the active architecture, and later calls D4b open.
- `pending_proposals/README.md` originally marked both documents closed while
  its practical order still said to finish R2, D3 and D4. This index has since
  been corrected to point at the master plan and retain R2/D3/D4 as closed;
  verify it during documentation closure, but do not list it as still broken.
- Qt transport test/module descriptions that say "Qt has no binary transport"
  must distinguish the lack of AnyWidget-style `buffers=` from the implemented
  payload-scheme binary transport.

Preserve the decision history, rejected alternatives, and measurements. Mark
obsolete execution sections explicitly as historical or replace them with the
actual final state. A new contributor reading from the index must not conclude
that closed phases remain implementation work.

## P1 — Measured pre-1.0 performance work

### 6. Build the JSON fallback lazily

This item remains owned by
[`lazy_json_fallback_payload.md`](lazy_json_fallback_payload.md). The binary path
currently avoids transmitting ViewerJSON but still builds the complete JSON
payload before binary negotiation consumes it. Historical pentalanine
measurements reported approximately 381 ms for ViewerJSON conversion versus 37
ms for array-native serialization, but that magnitude is not an acceptance
baseline: profiler overhead inflated at least one timing from this round, and
MolSysMT commit `b63a2f6c5` later removed a double deep copy. Repeat current
wall-clock A/B measurements against the pinned MolSysMT version. The
architectural conclusion (do not perform unused conversion) does not depend on
the old ratio.

Implement the fallback as a generation-bound lazy producer. The producer must
serialize the molecular system belonging to the failed generation, never a
newer `view.molsys` that replaced it while the stream was in flight.

Closure requires:

- `to_form("molsysmt.ViewerJSON")` is not called on a successful negotiated
  binary load;
- refused, failed and timed-out streams still deliver an equivalent JSON
  payload;
- the popup-targeted fallback keeps endpoint identity, including the cancel
  fixed in item 1;
- startup and retained-memory measurements are repeated at meaningful atom and
  structure counts;
- mutation check: restore eager construction and make the no-ViewerJSON test
  fail.

## P2 — Improvements to measure, not assumptions to implement

### 7. Measure endpoint-global scene deferral during popup bootstrap

There is one active binary stream and one S8 deferred-scene queue per view. While
a large canvas popup generation is being delivered, scene messages needed by
the already-loaded embedded host are also held so that the popup cannot observe
scene state before its structure.

This is correct but may make the host UI appear stalled during a large popup
bootstrap. Measure host interaction latency while opening a popup with a large
system. Only if the delay is material should the design evolve to endpoint-aware
delivery or per-endpoint queues. Any change must preserve S8 independently for
every receiver; sending early to the host must not let the popup receive early.

### 8. Measure copies and peak memory in the Qt binary scheme

Qt's payload-scheme transport is a sensible connector-specific implementation,
but assembling the structural buffers into one Python `bytes` object can create
a full transient copy before Qt/Chromium consume it. Record peak and retained
memory for representative solvated systems and multiple structures.

Do not replace this path merely because it is not AnyWidget `buffers=`. Change
it only if measurement shows a release-relevant peak and a lower-copy Qt API is
available without reintroducing large `runJavaScript` strings.

### 9. Retire the probe-induced Qt unknown-action asymmetry

R3 removed **silent** acceptance of unknown actions, but the two connectors are
not semantically identical:

- AnyWidget rejects an unknown browser action and does not forward it.
- Qt emits an observable `unknown_frontend_action` diagnostic and still forwards
  the event.

The current Qt policy exists because a payload-generation probe uses a synthetic
action that is not part of the product manifest. A test convenience is therefore
fixing product semantics at an authority boundary. Treat this as temporary debt
with an expiry, not an intentional long-term connector difference.

Declare the synthetic probe as an explicit transport/test action, then make Qt
strict as well. Mutation-test that an unknown action is diagnosed and never
reaches the view. Until that lands, document the actual asymmetry as inherited
from the probe, not as desired product policy.

## Product decisions adjacent to this audit

### 10. Decide the public persistence convenience separately from persistence

`export_state()` / `import_state()` version 2 already provide tested overlay
state persistence. They do not bundle the molecular system and require a
compatible structure to be loaded first.

Before 1.0, decide only whether users need small convenience methods such as
`save_state(path)` / `load_state(path)` around that existing contract. A portable
`.msv` package containing or resolving the molecular system needs a format,
versioning, provenance, and compatibility policy; it must not be implied by a
thin file wrapper and can remain post-1.0.

### 11. Keep the established post-1.0 boundaries

This audit found no reason to move the following into the 1.0 critical path:

- partial/windowed structure residency;
- workers, compression, shared memory and `SharedArrayBuffer`;
- Qt popout parity and automated Qt rendering on a GPU runner;
- camera acquisition and movie export;
- multiview and configurable picking.

`view.molsys` should remain a complete selected `molsysmt.MolSys`. Binary
transport and lazy fallback construction are optimizations of delivery, not a
reason to introduce a second scientific data model before 1.0.

### 12. Keep installation and onboarding as an explicit 1.0 gate

This audit did not execute a clean-environment installation or the public
one-line onboarding path. Their absence is not a transport defect, but they
remain release work: test installation from the supported package channels in a
fresh environment, then verify that `molsysviewer.view(molsys)` renders a demo
without repository-local state or undocumented setup. Record dependency/version
failures rather than masking them with the current development environment.

## Items delegated to the smoke-round inventory

The following remain part of the same correction programme. Their evidence and
acceptance steps live in
[`open_items_after_the_2026_08_smoke_round.md`](open_items_after_the_2026_08_smoke_round.md):

- **Z1:** declare `molsysviewer-sync-hierarchy` in the popup action manifest;
  the panel-popup System update path is currently rejected at runtime.
- **Z2:** declare `camera_stranded_inside_scene` in the browser-to-Python action
  manifest and test its complete seam; the S9 alarm is currently rejected before
  it can reach Python.
- **A1-A5:** run all browser E2Es and the performance suite; revalidate Qt and
  static HTML after camera authority; manually verify the final whole-reset fix.
- **B1-B3:** test the stranded-camera diagnostic and popup-size wiring, and add
  a transversal sender-to-manifest guard across both `actions` and
  `popup_actions` so another undeclared action cannot ship.
- **C1:** establish whether S8 deferral applies to Qt and test or document the
  connector-specific answer.
- **D1-D3:** lazy JSON fallback (expanded here as item 6), the hover-telemetry
  product decision, and filing the prepared Mol* camera report upstream.
- **E1-E5:** clean the resolved MolSysMT report and stale pending documents, and
  update the resume/checkpoint records with S8, S9 and the completed smoke round.

The broader pre-1.0 index also retains notebook execution in CI and scientific
dogfooding as release work. They were not re-audited here and therefore are not
silently reclassified as complete.

## Execution order

This audit no longer carries an independent recommended order. Follow
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md),
which begins with the broken distribution artifact and a green complete
baseline, then closes the active transport/manifest defects and transversal
guards before architectural rework. This document remains the evidence and
acceptance-detail record for its delegated items.
