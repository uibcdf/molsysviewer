# Pre-1.0 architecture rework and hardening master plan

**Status:** active master execution plan. Phases 0a through 4b are audited and
closed. Phase 5 is implemented and awaiting independent audit.

**Purpose:** turn the current, functionally strong viewer into a pre-1.0 base
that is robust under real connector lifecycles, efficient for scientifically
representative systems, easier to extend, and explicit about the compromises it
still keeps.

This plan supersedes the execution order in the audit inventories. Those remain
the evidence and defect records:

- [`open_items_after_the_2026_08_smoke_round.md`](open_items_after_the_2026_08_smoke_round.md);
- [`transport_popup_audit_followups_2026_08.md`](transport_popup_audit_followups_2026_08.md).

Normative scene behavior continues to live in
[`../scene_contracts.md`](../scene_contracts.md). If this plan and a scene
contract disagree, the contract wins until it is deliberately amended in the
same change as the implementation.

---

## Execution dashboard

Progress is the fraction of explicit acceptance items completed, not a
subjective estimate. Implementation does not close a slice: closure requires
the recorded validation, mutation evidence where applicable, and independent
audit.

| Slice | Deliverable | Status | Progress | Implementation / commit | Validation / audit |
|---|---|---:|---:|---|---|
| 0a | Distribution rescue | ✓ | 100% | working tree from `6362914c` | wheel import + metadata guard; audited and closed |
| 0b | Green baseline and thresholds | ✓ | 100% | `main` working tree | green baseline, timing/RSS bands and unavailable real-window surfaces recorded; audited and closed |
| 1 | Immediate correctness and transversal guards | ✓ | 100% | working tree from `6362914c` | seams and guards mutation-verified; audited and closed |
| 2 | Transfer state machine | ✓ | 100% | working tree from `6362914c` | transition and terminal cleanup guards mutation-verified; audited and closed |
| 3 | Direct lazy JSON fallback and deadline hardening | ✓ | 100% | working tree from `21027309` | lazy fallback, deadline and real-Mol* fallback path validated; audited and closed |
| 4a | Canonical static export | ✓ | 100% | working tree from `d7768ab1` | generated Python projection passed in real Chromium/Mol*; mutation-verified; audited and closed |
| 4b | Live `ready`/reconnect closure | ✓ | 100% | working tree from `2b504d77` | canonical ready projection, bounded compatibility path and real widget-seam E2E; audited and closed |
| 5 | Endpoint isolation and lifecycle | ● | 100% | `6904aea8` plus working tree from `1a9b59b1` | Per-endpoint transfer managers and queues; endpoint matrix closed; 1295 Python + 3 skips, 271 JS, tsc 0, runtime/perf, 30/30 E2E; 95k host latency 0.0111 ms; awaiting independent audit |
| 6 | Ownership audit and limited consolidation | ● | 100% | working tree from `0f907ccd` | Ownership table recorded; endpoint lifecycle consolidated in one registry; static projector remains single authority; 1298 Python + 3 skips; three guards mutation-verified; awaiting independent audit |
| 7 | Missing seam evidence | ○ | 0% | — | — |
| 8 | Representative performance and memory gate | ○ | 0% | — | — |
| 9 | Documentation and upstream closure | ○ | 0% | — | — |
| 10 | Product and release gates | ○ | 0% | — | — |

Status vocabulary:

- `○` — not started;
- `◐` — in progress;
- `●` — implemented, awaiting independent audit;
- `✓` — audited and closed;
- `⚠` — blocked, with the blocking condition and owner recorded;
- `⊘` — waived under an option explicitly allowed by this plan, with approver,
  date, residual behavior and post-1.0 destination recorded.

### Reporting protocol

Open a slice by changing only its row to `◐` and recording the working branch or
starting commit. At most one implementation slice should normally be in
progress; a validation-only slice may overlap when it cannot mutate the same
surface.

Each progress report records:

```text
slice:
status and completed acceptance items:
files / commits:
tests observed (command, pass/fail/skip totals):
mutation ledger entries:
real-seam evidence:
what was not done:
risks or blockers:
next bounded step:
```

When implementation is believed complete, set the row to `●`, not `✓`. After
independent review, add the audit result and commit to the row and set `✓`, or
return it to `◐` with the rejected criteria named. A waiver never masquerades as
completion and does not erase its deferred work.

Dashboard updates belong in the same commit as the evidence they report, except
for an auditor's closure note, which may be a following documentation-only
commit. Test totals are observed values; never copy expected totals from an
earlier report.

---

## 1. Why a rework is justified

The completed work established the right concepts:

- Python is the only reproducible mutation authority;
- R1 validates identity, direction and duplicate commands;
- R2 projects current scene state instead of replaying interaction history;
- D4 transports materialized structural arrays without text JSON;
- S8 prevents scene state from overtaking its molecular generation;
- S9 makes framing explicit instead of trusting half-built Mol\* bounds;
- state v2, one scene history, region recipes, layered colour and order have
  normative contracts.

Those decisions should survive. Some implementations beneath them should not be
treated as final merely because they work:

- the active binary stream is an untyped dictionary owned by a 3,400-line
  `core.py`;
- destination, generation, deadline, fallback and retained buffers are copied
  manually across cancellation paths, and one path already forgot the popup
  destination;
- the JSON fallback is built eagerly on every successful binary load;
- S8 has one view-global deferred queue even when only one popup is loading;
- interactive popups use a canonical snapshot, while static export still uses
  an append-only message journal;
- orchestration remains concentrated in `core.py`, `index.ts`,
  `viewer-controller.ts` and `state-handlers.ts`;
- large unit suites did not expose seven failures across serialization, timing,
  popup-only layout and real Mol\* state.

The correct response is not a general rewrite. It is a staged replacement of
the implementations whose ownership or state model is demonstrably weak.

---

## 2. Quality target

For 1.0, "fast, light and robust" means:

1. **Scientifically exact.** Missing box or time remains missing. Structure
   order, units, indices, recipes and visible state are never invented or
   silently changed.
2. **One authority.** Python owns reproducible state; browser endpoints project
   it. Connector adaptation does not create a second scene model.
3. **Bounded by current work.** Popup bootstrap and export scale with current
   scene content, not the number of past interactions.
4. **No avoidable amplification.** A negotiated binary load does not build
   ViewerJSON, nested coordinate lists or text JSON unless fallback is actually
   required.
5. **Endpoint-correct.** Generation, cancellation, fallback and deferred scene
   messages cannot cross host, popup, session or connector boundaries.
6. **Observable failure.** Rejection, timeout, corruption and fallback leave a
   diagnostic. Cleanup failures may not silently invalidate the primary result,
   but they must remain inspectable.
7. **Growth by owner.** Transport, projection, lifecycle and scene domains have
   modules with explicit ownership instead of accumulating in global
   orchestrators.
8. **Evidence at the real seam.** Serialization and rendering claims are tested
   through the connector and, where relevant, against real Mol\* and WebGL2.
9. **Extensible without hidden loss.** Shipped add-on behavior survives the
   supported persistence/bootstrap targets. Unsupported arbitrary add-on state
   is declared as such; removing a journal cannot silently narrow an existing
   guarantee.
10. **Installable from the artifact.** A wheel/conda package contains every
    runtime resource and declares the dependencies its imported modules require.

---

## 3. Decisions that remain fixed

This plan does **not** reopen:

- `view.molsys` as the complete selected `molsysmt.MolSys`;
- Python as mutation authority;
- the R1 envelope and shared action manifest;
- the canonical-current-state principle of R2;
- state document version 2 and the distinction between state and undo history;
- scene Contracts A-S9 unless a discovered defect requires a recorded
  amendment;
- Mol\* as rendering engine;
- the public manager API and API-first layering rule;
- the Qt payload-scheme approach merely because it differs from AnyWidget
  `buffers=`;
- complete materialization for 1.0.

Windowed residency, workers, compression, shared memory, multiview, Qt popout,
configurable picking, camera acquisition and movie export remain post-1.0 unless
a new measured release blocker changes that decision.

Established facts that the rework must preserve:

- live `initial_messages` and the current `ready` replay do not double-apply the
  scene: the former is populated for static HTML export, while the latter is the
  live-widget path. Canonical snapshots may replace both implementations, but
  must still apply each projection exactly once;
- Qt does not use the AnyWidget `_binary_structure_stream`. Its payload-scheme
  bridge owns a separate ordered queue and acknowledgement flow. Contract S8
  must be proved on that queue rather than by copying the AnyWidget manager;
- real-GPU Qt rendering in CI remains a deliberate post-1.0 item. Manual
  revalidation after later camera and representation changes is a separate
  pre-1.0 obligation.

---

## 4. Work classes

### A. Must correct

- targeted binary fallback sends an untargeted cancel;
- `molsysviewer-sync-hierarchy` is emitted but absent from `popup_actions`;
- `camera_stranded_inside_scene` is emitted browser-to-Python but absent from
  `actions`, so the S9 diagnostic is rejected before Python can observe it;
- the built wheel omits `runtime_actions.json`, which is loaded during import,
  and its metadata omits direct runtime imports such as NumPy and MolSysMT. A
  source checkout working does not make the distribution artifact importable;
- Qt forwards unknown actions because a synthetic payload-generation probe is
  undeclared. That is temporary test-shaped product policy, not a permanent
  connector distinction;
- retained design documents contradict the shipped R2/D3/D4 and Qt state;
- stale pending/checkpoint documents still describe completed or superseded
  work as open.

### B. Must rework

- binary transfer lifecycle: replace the stream dictionary with a typed state
  machine and manager;
- fallback construction: make it lazy and generation-bound;
- static export bootstrap: project current state instead of treating the
  message journal as scene authority;
- embedded `ready`/reconnect bootstrap and any rebuild path that still replays
  `_message_history`: either move them to the current-state projector family or
  explicitly bound and document the remaining live journal before 1.0;
- add-on state/projection participation: preserve shipped behavior in static
  export, but do not create a public third-party extension API before 1.0 without
  a demonstrated consumer;
- orchestration ownership: extract the Python transport and projection state
  required by this rework. Broad frontend decomposition is post-1.0 unless a
  correctness change cannot obtain single ownership without it.

### C. Must harden

- widget/kernel session replacement;
- D3 deadline semantics and cleanup scheduling;
- sender-to-manifest consistency across both `actions` and `popup_actions`,
  including direction/category compatibility;
- S8 on every connector and endpoint;
- the complete camera diagnostic seam, static HTML and Qt behavior after S9;
- popup sizing and hierarchy updates;
- wire serialization of NumPy and quantity-derived values;
- clean close/dispose paths and retained-memory checks;
- built-package contents and declared runtime dependencies;
- tests that currently assert private `_message_history` contents instead of
  public state, emitted wire behavior or rendered outcome.

### D. Must measure before changing

- endpoint-global deferral during popup bootstrap;
- Qt transient copies;
- browser native/GPU memory;
- scene-history snapshot memory at its 25-entry limit, including large literal
  shapes and annotations;
- built wheel/conda size, cold import and first-view cost;
- large atom-count and structure-count behavior;
- whether representation overlap during add-before-remove creates a material
  peak;
- any event-loop implementation proposed for strict wall-clock expiry.

### E. Product/release work

- clean installation and dependency-channel synchronization;
- one-line onboarding;
- scientific dogfooding;
- notebook execution in CI;
- the decision about thin `save_state`/`load_state` file helpers;
- the opt-in hover-telemetry semantic decision;
- filing the prepared Mol\* camera-bounds report.

---

## 5. Target transport design

### 5.1 `StructureTransfer`

Replace the mutable stream dictionary with a typed object. Its required state is:

```text
StructureTransfer
  identity
    viewer_id
    session_id
    stream_id
    generation
  destination
    connector
    endpoint_id | embedded-host
  state
  deadline
  awaiting_ack
  next_chunk
  chunks
  retained_payload
  lazy_json_fallback
  deferred_scene
```

The exact Python representation may use dataclasses and enums. Callers must not
reach into its fields to perform transitions.

### 5.2 State machine

```text
CREATED
  -> BEGIN_SENT
  -> STREAMING
  -> WAITING_COMPLETE
  -> COMPLETED

Any non-terminal state may transition to:
  -> CANCELLED
  -> EXPIRED
  -> FALLBACK
```

Terminal transitions release retained arrays exactly once. A late ack is
rejected by identity/generation and cannot resurrect a terminal transfer.

### 5.3 `StructureTransferManager`

The manager owns:

- active transfers by destination;
- generation allocation;
- ack validation and state transitions;
- cancellation and replacement;
- deadline checks;
- fallback invocation;
- deferred-scene release;
- close/dispose cleanup;
- transport diagnostics.

`MolSysView` delegates to it. The manager does not own molecular selection,
scene state or public API semantics.

### 5.4 Destination invariants

Destination is part of transfer identity, not optional metadata added at send
time. Begin, chunks, complete, cancel and fallback all derive their target from
the same object. A popup transfer cannot fall back into the host.

### 5.5 Direct lazy JSON fallback

The fallback is a callable bound to the molecular generation being transferred.
It must not read whichever `view.molsys` happens to be current later. A newer
load may replace the view while the older transfer is awaiting an ack.

ViewerJSON is not an internal MolSysViewer representation. The successful
binary path must perform no portable-JSON construction. Refusal, timeout and
connector failure build the existing wire JSON directly from the transfer's
bound `molsysmt.MolSys` revision.

### 5.6 Deadline policy

No timer thread may call `widget.send`. First preserve the cooperative policy:
expiry is applied on the first safe kernel entry after the deadline. Then probe
the owning event loop. A stricter callback is adopted only if it demonstrably
runs on the safe widget thread in supported notebook environments.

### 5.7 Endpoint-aware S8

The new manager must make endpoint ownership explicit from the start. Whether
different endpoints may progress concurrently is decided by measurement in
Phase 5. Until then, behavior may remain serialized, but the model must not
require returning to a view-global anonymous stream dictionary.

---

## 6. Target projection and export design

### 6.1 One current-state projector family

Generalize the current popup projector to explicit targets:

```text
build_scene_snapshot(target)
  canvas-popup
  panel-popup
  static-export
  embedded-runtime  # optional Phase 4b closure
```

Targets share domain projectors and differ only in their declared projection
profile. They do not filter an arbitrary journal after the fact.

### 6.2 Embedded readiness and reconnect

The live widget still handles `ready` by replaying `_message_history`. The
preferred closure replaces that authority with the canonical embedded-runtime
snapshot, so a reconnect receives current state once rather than every operation
that led to it. Because this migration also changes Contract S1 and pressures a
new add-on extension surface, Phase 4b may instead retain a measured, explicitly
bounded journal for 1.0 and defer canonical live bootstrap.

This migration includes tests whose only assertion is the position or contents
of a private history list. Replace them with assertions against public state,
captured connector delivery or rendered state. Tests must not force retention of
an obsolete journal implementation.

Under canonical closure, migrate private-history tests to public state, captured
connector delivery or rendered state, and amend Contract S1 in the same change.
Under contained deferral, keep tests for the intentionally retained journal's
bound and explicit summary resend. System-edit rebuilds and other replay helpers
remain a separate inventory: live-registry reconstruction stays; journal-based
authority is either migrated or named and bounded.

### 6.3 Static export

Python exists while HTML is built, even though it will not exist when the file
is opened. Build and embed the canonical static snapshot at export time. The
browser then consumes that snapshot without asking Python.

The static target must include everything required to recreate the current
visible scene, camera, structure, frame, selections, regions, objects, sections,
whole state, colours, layers and addon projection state supported by export.
Contract language that calls camera state "never" part of a Python snapshot must
be amended for this target: live camera remains endpoint-local, while export
captures it before the host disappears.

### 6.4 `_message_history`

Audit every remaining reader and classify it:

- static current-state bootstrap -> replace with canonical projection;
- live current-state bootstrap -> canonicalize or retain only with the Phase 4b
  bounded-journal waiver;
- undo/redo -> belongs to `SceneHistory`, not the message journal;
- diagnostics or narrative replay -> retain only with an explicit bounded
  policy and name;
- obsolete compatibility -> remove.

The journal must not remain an unbounded accidental source of truth. If a
command-history product is desired later, it receives its own contract and
compaction policy.

### 6.5 Add-on projection and state boundary

Managed add-on output that becomes a normal shape, annotation, measurement,
layer or region is already covered by those domain registries. Arbitrary
per-view state created through an add-on `state_factory` is not currently part
of state v2, and `AddonExportHelperSpec` describes export UI helpers rather than
a scene-snapshot contribution.

First inventory shipped add-ons and preserve the output already covered by core
domain registries. If a shipped pre-1.0 behavior requires arbitrary add-on state
to survive export or canonical reconnect, define the smallest opt-in hook with
explicit ownership, for example:

```text
export_state(view) -> JSON-compatible addon state
import_state(view, state)
build_projection(view, target) -> ViewerMessages
```

The final names are a design decision. If hooks are introduced, these
requirements are not negotiable:

- disabled or unavailable add-ons are handled observably;
- one add-on cannot write another add-on's namespace;
- contributions are JSON/wire validated;
- projection order relative to molecular load and core scene objects is
  declared;
- equal add-on state produces equal snapshot content;
- state format/version compatibility is explicit;
- absence of a hook means no persistence claim, not best-effort hidden replay.

Add a shipped or fake add-on projection test whose state would be lost if its
required hook were removed. If no hook is introduced, document that arbitrary
`state_factory` data has no persistence/export guarantee and defer the public
extension contract to post-1.0.

### 6.6 Projection fidelity

For equal live state, each canonical snapshot target has equal content and size
regardless of whether the user performed 10 or 100,000 intermediate operations.
Dynamic regions use the current evaluated indices. Missing box/time remain
absent. A pristine whole is represented by silence where silence and explicit
`None` have different Mol\* effects.

---

## 7. Target module ownership

This is extraction by responsibility, not a file-size exercise.

### Python

```text
molsysviewer/viewer/
  transport/
    transfer.py          # state and transitions
    manager.py           # active transfers and deadlines
    connectors.py        # connector capabilities/adaptation
  projections/
    scene.py             # shared domain projection
    popup.py             # endpoint profiles
    export.py            # static profile
  runtime_dispatch.py    # validated event -> domain handler
```

`core.py` remains the `MolSysView` facade and composition root. Public behavior
does not move behind a second API.

### Longer-term TypeScript target

```text
js/src/runtime/
  widget-seam.ts
  structure-transfer.ts
  endpoint-lifecycle.ts
  popup-bootstrap.ts
```

`index.ts` composes these services. `viewer-controller.ts` remains the visual
facade but delegates lifecycle/transport work. Existing domain handler modules
remain the owners of scene mutations.

This is a post-1.0 direction by default, not a required pre-1.0 file move. The
pre-1.0 work extracts TypeScript only where a phase would otherwise leave one
piece of mutable transport/lifecycle state with multiple owners.

### Extraction rules

- one owner per state variable;
- no circular imports;
- no duplicate compatibility paths;
- no public API change merely to enable extraction;
- no behavior change hidden inside a structural commit;
- every extraction commit leaves all tests green.

---

## 8. Execution phases

### Phase 0 — Distribution rescue, baseline and quarantine

#### Phase 0a — Distribution rescue

1. Record `HEAD`, worktree state and the known `sandbox/` exclusions.
2. Build the actual wheel before trusting the checkout, and inspect the conda
   recipe against the same resource/dependency contract. Full clean-channel
   conda resolution belongs to Phase 10 because the UIBCDF dependency stack is
   not yet version-closed.
3. Include `runtime_actions.json` and every required runtime resource in the
   installed package. Audit direct imports against wheel metadata and conda
   recipes; declare required dependency names, including NumPy and MolSysMT,
   without introducing speculative version pins. Version/channel compatibility
   is a separate Phase 10 gate.
4. Leave a reproducible artifact smoke check in the repository. It must build
   the wheel, install it with `--no-deps` outside the source tree, import it with
   a known-compatible dependency environment, load `runtime_actions.json`
   through the installed resource API and inspect installed metadata for
   required direct dependency names. A one-off successful shell session is
   evidence, not a regression guard.

**0a exit:** the isolated wheel import uses packaged resources successfully, and
wheel/conda metadata name all direct runtime dependencies without claiming
unvalidated version compatibility.

#### Phase 0b — Green baseline

1. Run the current required suites once, explicitly including all real-browser
   E2E suites and `npm run test:perf`, and record wall time, RSS and browser
   environment. Phase 0 does not close on a red baseline: diagnose each failure
   and restore green before architecture work begins.
2. Capture transport/load baselines before changing implementation.
   Preserve the comparison point in
   `devguide/performance/message_path_regression_check_2026_07.md`, including
   the approximately 0.3-0.4 ms unknown-message toll at 95,000 atoms and the
   approximately 0.0008 ms/frame dynamic-region measurement.
3. For every measured gate, record the noise band and acceptance threshold
   before implementation. Later phases may not decide what "material" means
   after seeing their result.
4. Freeze the existing wire messages and scene contracts with focused tests.
5. Mark the two audit inventories as evidence owned by this plan.
6. Before the rework changes these paths, record the available real-surface
   baseline: Qt real-window framing/zoom, static HTML framing and representation
   replacement, panel-popup hierarchy after a second load, and
   load-reload-hide/show with a clean browser console. An unavailable display or
   browser is reported as unavailable, never treated as a pass.

Only packaging/metadata corrections and fixes required to establish an honest
green baseline enter this phase; runtime architecture does not.

**0b exit:** the complete baseline is green, recorded and paired with
predeclared regression thresholds.

### Phase 1 — Immediate correctness and transversal guards

1. Fix popup-targeted fallback cancellation.
2. Declare `molsysviewer-sync-hierarchy` in `popup_actions`.
3. Declare `camera_stranded_inside_scene` in `actions` with the category used by
   the equivalent viewer-initialization diagnostic.
4. Add a structural sender-to-manifest guard for both governed seams. Prefer
   typed sender wrappers or an AST/source extractor over a brittle action count
   or broad grep: every statically emitted action must exist in the appropriate
   manifest section with a compatible direction/category.
5. Add host and popup tests for targeted cancel-before-fallback.
6. Add real path tests for hierarchy resynchronization and for the complete S9
   diagnostic delivery; a one-line manifest declaration alone does not close
   either defect.
7. Make a manifest-contract rejection observable through the runtime diagnostic
   path, not only through a transient browser console message. Test the
   diagnostic as well as the refusal.
8. Declare the synthetic Qt payload-generation probe as an explicit
   transport/test action, then make Qt reject unknown product actions after an
   observable diagnostic, matching the AnyWidget authority boundary. Do not
   preserve permissive product behavior merely to keep an undeclared test probe
   working.
9. Make transport cleanup failures observable without masking the primary
   failure.

**Exit:** the three active message-path defects are closed and
mutation-verified; a new undeclared action on either governed seam fails the
transversal guard; and unknown actions have the same strict authority semantics
in Qt and AnyWidget.

#### Phase 1 implementation evidence — 2026-08-02

Implemented on the same uncommitted working tree as Phase 0, pending independent
audit:

- popup-targeted fallback cancellation now preserves `target_endpoint_id` on
  both the cancel and JSON fallback; the focused structure-relay E2E confirms
  the cancel reaches the addressed popup with generation and reason intact;
  normal cancellation and fallback share one cancel builder/transmitter;
- cancellation-send failures are reported through the suppressed-exception
  diagnostic seam without masking fallback or stream release;
- the shared manifest now declares the live browser emissions, the System
  hierarchy popup projection, the runtime-contract diagnostic and an isolated
  Qt-only test probe;
- an AST-based transversal test derives static `notify`/`sendToPython`,
  `sendToHost` and `popupMgr.send`/`sendTo` callsites from `js/src` and verifies
  their manifest category/direction;
- rejected widget and popup messages produce `runtime_contract_rejected` at the
  Python diagnostic authority even when `debug_js` is false;
- Qt now reports and refuses unknown product actions, while its payload test
  uses the explicitly declared `qt_payload_probe` action;
- the popup hierarchy test crosses the authenticated `postMessage` channel,
  and the S9 test exercises the inside-scene condition before verifying the
  envelope-to-SMonitor path.

Observed validation:

| Gate | Result |
|---|---:|
| `python -m pytest --receptor=llm -n 12 tests/` | 1165 passed, 3 documented skips, exit 0 |
| `npm run test:js` | 265 passed, exit 0 |
| `npx tsc --noEmit` | exit 0 |
| `npm run build:runtime` | exit 0 |
| `npm run test:perf` | exit 0; 95k unknown 0.20 ms, hide 0.10 ms, dynamic 0.000633 ms/frame |
| `npm run test:e2e` | 28/28 suites, Chrome 149, WebGL2/SwiftShader, exit 0 |

The full Python run preceded the final helper-only consolidation of cancel
construction/transmission; its two focused regression tests passed on the
consolidated code. Likewise, the full JS run preceded the final tightening of
the test-only AST guard; the focused guard passed afterward. No production
TypeScript changed after the full JS/build/E2E gates.

Mutation ledger:

| Mechanism | Mutation | Test that failed | Restored result |
|---|---|---|---|
| targeted fallback cancellation | omit popup destination from cancel | `test_a_popup_targeted_stream_fallback_cancels_and_loads_the_same_endpoint` | pass |
| cleanup observability | swallow fallback-cancel exception | `test_a_failed_stream_cancel_is_reported_without_masking_the_json_fallback` | pass |
| browser manifest direction | move `camera_stranded_inside_scene` from browser actions to Python-only `outbound_requests` | `every static browser sender is declared...` | pass |
| popup manifest coverage | remove `molsysviewer-sync-hierarchy` | AST popup guard and `popup-channel.e2e` | pass |
| Qt authority boundary | forward after unknown-action diagnostic | `test_an_unknown_action_is_observable_and_refused_on_qt_as_on_anywidget` | pass |
| popup refusal observability | remove host rejection callback | `the host refuses to emit an action...` | pass |
| S9 condition | suppress the inside-scene report | `camera S9 diagnostic reports...` | pass |
| widget refusal observability | suppress the diagnostic envelope | `widget-seam.e2e` | pass |

Not done in this slice: no transfer state machine, lazy fallback construction,
canonical export or orchestrator decomposition; those remain Phases 2 onward.
No dependency versions were pinned: resolver/channel closure remains Phase 10.
The developer-owned `sandbox/Smoke_Test.ipynb` was neither used as evidence nor
included in the implementation.

### Phase 2 — Transfer state machine

1. Introduce `StructureTransfer` and its transition tests.
2. Introduce `StructureTransferManager` behind the current `MolSysView` seam.
3. Move generation, ack, cancellation, release and deadline ownership.
4. Preserve AnyWidget and Qt wire behavior.
5. Remove the old stream dictionary only after parity tests pass.
6. Enumerate and test every terminal transition (`COMPLETED`, `CANCELLED`,
   `EXPIRED`, `FALLBACK`): retained data is released exactly once, destination
   and generation remain correct, and a late acknowledgement cannot revive it.

**Exit:** a structural check finds no direct transfer-state transition in
`core.py`, and parameterized transition tests prove release-once and identity
for every enumerated terminal state.

#### Phase 2 implementation evidence — 2026-08-02

Implemented on the combined uncommitted Phase 0-2 working tree, pending
independent audit:

- `StructureTransfer` is the explicit state machine for one molecular
  generation; its active states are waiting for begin, chunk or completion,
  and its terminal states are `COMPLETED`, `CANCELLED`, `EXPIRED` and
  `FALLBACK`;
- `StructureTransferManager` owns generation allocation, the active transfer,
  identity matching, acknowledgement progress, deadlines and terminal
  detachment;
- terminalization releases retained payload arrays and chunk memoryviews once;
  repeated terminal calls and late acknowledgements cannot alter the detached
  generation;
- `MolSysView` now reacts to typed transfer results and owns only external
  effects: connector sends, diagnostics, JSON fallback and the S8 deferred
  scene queue;
- the old `_binary_structure_stream`, generation counter and direct state
  mutations were removed from `core.py`; a structural regression test enforces
  that ownership boundary;
- existing AnyWidget streaming, popup-targeted fallback, timeout and S8 tests
  were migrated to observe the manager, while focused Qt tests confirm its
  independent queue/wire behavior is unchanged.

Observed validation:

| Gate | Result |
|---|---:|
| focused transfer/timeout/S8/runtime seam | 39 passed, exit 0 |
| focused Qt transport/standalone | 44 passed, 2 documented real-window skips, exit 0 |
| `python -m pytest --receptor=llm -n 12 tests/` | 1178 passed, 3 documented skips, exit 0 |

No TypeScript source or frontend wire schema changed in Phase 2, so the Phase 1
JS, typecheck, runtime-build, performance and browser results remain the
applicable frontend baseline rather than being rerun mechanically.

Mutation ledger:

| Mechanism | Mutation | Test that failed | Restored result |
|---|---|---|---|
| terminal immutability/release-once | allow a second terminal transition | `test_every_terminal_transition_releases_once_and_preserves_identity` | pass |
| active-transfer ownership | allow `start()` to overwrite a live transfer | `test_start_refuses_to_overwrite_an_active_transfer` | pass |
| acknowledgement identity | accept a foreign session/generation | `test_only_the_expected_ack_advances_and_refreshes_the_deadline` | pass |
| core ownership boundary | reintroduce `_binary_structure_stream` in `core.py` | `test_core_orchestrates_transfer_effects_without_owning_transfer_state` | pass |

Not done in this slice: fallback construction remains eager and completion-wait
deadline semantics remain unchanged; those are Phase 3. The Qt bridge keeps its
separate ordered payload queue by design. No frontend orchestrator was split,
no dependency version was pinned, and no developer notebook was used or
modified by this phase.

### Phase 3 — Direct lazy JSON fallback and deadline hardening

1. Bind a lazy fallback to the transfer's molecular generation.
2. Remove ViewerJSON from product Python; share canonical topology extraction
   between direct JSON and array-native encoders.
3. Prove successful binary delivery never constructs portable JSON.
4. Prove refusal, failure and timeout construct and deliver equivalent direct
   JSON exactly once.
5. Preserve S8 ordering across fallback.
6. Evaluate safe event-loop expiry; retain and document cooperative expiry if
   portability is not demonstrated.
7. Re-run load and memory benchmarks.

**Exit:** eager fallback cost is absent from the success path and timeout
semantics are both tested and accurately documented.

Implementation note (2026-08-02): no portable owning-loop handle is exposed by
the supported AnyWidget hosts. The cooperative deadline remains the deliberate
closure: expiry occurs on the first relevant kernel-thread entry after the
deadline. A timer thread remains forbidden because it could call `widget.send`
off the connector's safe thread. The injected-clock tests cover deterministic
release on that next entry.

Implementation report (working tree from `21027309`):

- ViewerJSON was removed from product Python rather than retained as a lazy
  intermediate. `json_molsys.py` and the array-native encoder share one
  canonical topology extractor and read structures directly from MolSys.
- Loads and rebuilds register a memoized `LazyMolecularMessage` bound to a
  molecular revision. Successful binary delivery never materializes it;
  non-binary delivery, timeout, connector failure, popup JSON and static export
  materialize ordinary dictionaries at their explicit boundary.
- Transfer fallback factories capture their exact allocated generation. Reset
  and rebuild cancel an older stream before replacing its projection.
- Missing box/time remain missing. Present coordinates/box/time are converted
  explicitly to angstrom/angstrom/ps at the JSON boundary.
- The startup and trajectory benchmark tools now measure the live direct-JSON
  and array-native paths instead of importing the removed serializer.

Observed validation:

| Check | Result |
|---|---|
| focused lazy/transfer/load/export set | 33 passed |
| `python -m pytest --receptor=llm -n 12 tests/` | 1186 passed, 3 documented environmental skips |
| benchmark/tool Python syntax | exit 0 |
| `npx tsc --noEmit` | exit 0 |
| direct-JSON E2E build | exit 0 |
| direct-JSON E2E browser launch | blocked before test: sandbox denied Chrome crashpad socket (`SIGTRAP`) |

Mutation ledger:

| Mechanism | Mutation | Test that failed | Restored result |
|---|---|---|---|
| molecular revision guard | accept a stale revision | `test_lazy_projection_rejects_a_stale_molecular_revision_before_building` | pass |
| exact fallback generation | read the manager's later generation | `test_fallback_factory_is_bound_to_the_transfer_generation` | pass |
| zero JSON on binary success | force materialization before array serialization | `test_anywidget_binary_capability_never_builds_the_json_fallback` | pass |
| lazy marker containment | return the internal marker from export | `test_build_export_messages_captures_reproducible_workbench_state_end_to_end` | pass |

Not done: the real-Mol* JSON assertion has been added to
`export-replay.e2e.ts`, but this executor cannot launch Chrome. Run it with the
Python-generated payload in the established browser/WebGL environment before
moving this row to implemented/awaiting audit. No dependency versions were
pinned, no general frontend refactor was started, and the sandbox notebook was
not used or modified by this phase.

```bash
python devtools/benchmarks/trajectory_transport_baseline.py emit-payload \
  --case dialanine-1 --output /tmp/molsysviewer-phase3-direct-json.json
cd molsysviewer/js
MSV_E2E_MOLSYS_PAYLOAD=/tmp/molsysviewer-phase3-direct-json.json \
  npm run test:e2e:export
```

### Phase 4 — Canonical static export and bounded live bootstrap

#### Phase 4a — Canonical static export (required pre-1.0)

1. Inventory all `_message_history` writers/readers and isolate the static-export
   readers.
2. Add a static-export projection profile and switch HTML/docs export to current
   state rather than interaction history.
3. Amend the camera contract in the same change: camera remains endpoint-local
   and ephemeral for live hosts, but a static export must capture and embed the
   camera needed to reproduce the exported view because no host exists later.
4. Audit shipped add-ons and preserve every currently supported static-export
   contribution. Do not create a public third-party projection API solely for
   hypothetical future consumers; document unsupported arbitrary
   `state_factory` state explicitly if no shipped contract promises it.
5. Validate structure, camera, frame, representation changes and all supported
   persisted scene domains in a real exported browser artifact.
6. Prove equal current scenes produce equal snapshot content/size after 10 and
   100,000 irrelevant interactions.

**4a exit:** static export no longer reads an append-only journal, its camera
semantics are normative, and its size is invariant to irrelevant interaction
count.

**Implementation report (2026-08-02).** `_build_export_messages()` now delegates
to a dedicated static target built on the canonical canvas projection. It
reconstructs the current molecular generation, scene look, whole, layers,
regions, shapes, annotations, measurements, sections, visibility, colours,
selections, frame and player state from live registries; it never reads
`_message_history`. The static target then adds current figure state, the
materialized add-on runtime/export-helper summary and the captured camera, in
that order, with camera last. Live popup targets continue to exclude camera.

The old history cleaner was removed rather than retained as a compatibility
fork. HTML standalone/lite, headless image paths and the Qt bootstrap already
share `_build_export_messages()`, so they now consume the same canonical static
projection. A latent authority defect exposed by the migration was fixed:
`CameraManager.set_snapshot()` now records the applied snapshot in Python, so
static export does not depend on finding the command in a journal.

Shipped add-on output that enters core scene registries remains covered, and
the existing materialized section/export-helper summary remains present.
Arbitrary `state_factory` fields still have no persistence or static-export
guarantee; this is now stated in the developer add-on guide. No hypothetical
third-party projection API was added.

Validation observed:

- `pytest --receptor=llm tests/ -n 12`: **1190 passed, 3 skipped**;
- `npm run test:js`: **265 passed**;
- `npx tsc --noEmit`: **exit 0**;
- focused canonical/export files: **79 passed**, plus the static snapshot and
  exact standalone-wrapper checks;
- a Python fixture containing two structures, a styled/hidden region, shape,
  annotation, measurement, saved selection, frame 1, whole representation and
  camera was replayed in Chromium against real Mol\*: **passed**. The browser
  asserted the Mol\* structure atom count, whole/region representation cells,
  region visibility, tagged shape ref, annotation, measurement, frame and
  camera. Reproduce with:

```bash
python devtools/e2e/build_static_export_fixture.py /tmp/molsysviewer-phase4a-export.json
cd molsysviewer/js
npm run build:harness
npx esbuild tests/e2e/export-replay.e2e.ts --bundle --platform=node --format=esm \
  --outfile=tests/e2e/export-replay.e2e.js --external:playwright \
  --external:chromium-bidi/\*
MSV_E2E_EXPORT_MESSAGES=/tmp/molsysviewer-phase4a-export.json \
  node tests/e2e/export-replay.e2e.js
```

Mutation ledger:

| mechanism | mutation | test | observed result |
|---|---|---|---|
| static export ignores the append-only journal | return `list(_message_history)` from `_build_export_messages()` | `test_static_export_content_and_size_ignore_one_hundred_thousand_history_entries` | fails with 100,000 extra messages; passes restored |
| hostless export embeds camera while live popup does not | suppress the static camera append | `test_static_export_embeds_hostless_state_that_live_popup_excludes` | fails because add-on summary becomes final op; passes restored |

Not done: Phase 4b was not opened, no choice between canonical live bootstrap
and bounded-journal waiver was made, Contract S1 and ready/reconnect behavior
were not changed, and no public add-on state/projection hook was introduced.
Generated `viewer.js` was not rebuilt because no runtime TypeScript source
changed. The dirty sandbox notebook was not read or included.

#### Phase 4b — Live `ready`/reconnect (waiver candidate)

Choose and record one pre-1.0 closure when Phase 4b opens, before implementation
work begins. The choice may not be postponed until the end of the phase, when
cost already incurred or fatigue would bias the waiver decision:

- **Canonical closure:** add the embedded-runtime profile, switch
  `ready`/reconnect to it, amend Contract S1 from explicit `_sync_*_runtime`
  calls to outcome-based authoritative-summary coverage, and replace the old
  test with one that fails when a registered summary domain is absent from the
  canonical projection.
- **Contained deferral:** preserve Contract S1 and the explicit summary resend,
  give the remaining live journal a measured bound/compaction policy, document
  that reconnect still uses it, and move canonical live bootstrap plus any
  public add-on projection hook to post-1.0.

**Opening decision (2026-08-02): canonical closure.** The static and popup
projectors demonstrate that live registries already reconstruct the current
scene. Retaining an append-only command journal for `ready` would preserve a
second authority, memory growth proportional to interaction count and a
different reconnect path without a pre-1.0 benefit. The embedded-runtime target
will combine the canvas scene with authoritative panel/runtime projections,
without camera (endpoint-local) or duplicate selection/measurement-setting
messages. Once `ready` no longer reads `_message_history`, the remaining product
uses will be audited: obsolete generic-journal bookkeeping is removed rather
than bounded if no behavior consumes it. Coalesced per-domain records and
`SceneHistory` remain because they own current state and undo respectively.

Under either closure, replace tests that pin private history layout with
state/wire/render assertions where they do not protect an intentionally retained
journal contract.

**4b exit:** reconnect behavior, journal bound and Contract S1 mechanism agree
with each other and are mutation-verified. Deferral is recorded as a waiver, not
reported as canonicalization.

### Phase 5 — Endpoint isolation and lifecycle

The responsiveness threshold is fixed before measurement: while a canvas popup
has a large molecular generation in flight, a projection for the already-loaded
embedded host must be handed to its connector in less than **100 ms**. This is
the human-feedback boundary for the authority/transport seam, not a claim about
Mol* load or render time; the latter belongs to the Phase 8 scale matrix.

1. Measure host latency while a large canvas popup bootstraps.
2. If material, enable per-destination transfer progress and deferred queues.
3. Test widget reconstruction/kernel-session replacement end to end.
4. Test popup close during begin, chunk, completion wait and fallback.
5. Prove stale acks and stale sessions cannot mutate or retain state.
6. Close an explicit endpoint matrix: embedded AnyWidget host, canvas popup,
   panel popup and Qt standalone. Identity/cleanup apply to all live endpoints;
   S8 molecular ordering applies to embedded AnyWidget, canvas popup and Qt,
   while the panel popup must be proved free of molecular transfer state.

**Exit:** every row in the endpoint matrix has named identity, ordering and
cleanup tests. If serialization remains global, its measured latency and
predeclared acceptance threshold are recorded.

#### Phase 5 implementation evidence — 2026-08-08

Phase 5 replaces the view-global popup transfer gate with one manager and one
deferred queue per destination. The embedded host and a canvas popup can advance
independently; a panel popup owns no molecular stream; Qt continues to satisfy
S8 through its own ordered payload-reference queue rather than by sharing the
AnyWidget transfer manager.

The final audit found one lifecycle defect in the initial implementation. A
canvas manager was removed after each completed or fallback generation. A live
popup receiver retains its latest generation, so recreating the Python manager
reset the sender to generation 1 and made the popup reject the next molecular
reload as stale. An inactive manager now remains owned by its endpoint until
that endpoint closes; completion/fallback release its payload, while endpoint
close releases the manager itself.

Endpoint evidence matrix:

| Endpoint | Identity | Ordering / absence of molecular state | Cleanup |
|---|---|---|---|
| Embedded AnyWidget host | `test_the_widget_connector_envelopes_control_messages_on_the_wire`; `test_only_the_expected_ack_advances_and_refreshes_the_deadline` | `test_a_replayed_scene_waits_for_the_streamed_structure`; `array-native-load.e2e.ts`; `widget-seam.e2e.ts` | `test_every_terminal_transition_releases_once_and_preserves_identity`; `test_close_releases_embedded_and_popup_structure_transfers` |
| Canvas popup | `test_acknowledgement_must_belong_to_the_transfer_target_endpoint`; `the host binds a popup acknowledgement to its authenticated source endpoint`; `endpoint-lifecycle.e2e.ts` | `test_a_canvas_popup_snapshot_streams_the_molecular_generation_to_its_endpoint`; `popup bootstrap queues only that endpoint and flushes after initial sync`; `structure-data-relay.e2e.ts` | `test_popup_close_releases_every_active_transfer_state`; `test_a_popup_targeted_stream_fallback_cancels_and_loads_the_same_endpoint`; `endpoint-lifecycle.e2e.ts` |
| Panel popup | authenticated popup channel tests | `test_a_panel_popup_snapshot_never_starts_a_molecular_stream`; `sendTo delivers to one popup endpoint, so a canvas bootstrap never reaches a panel popup`; `test_live_molecular_reload_starts_independent_host_and_canvas_generations` | `closing a popup reports its exact endpoint once`; `test_closing_panel_endpoint_does_not_release_canvas_transfer` |
| Qt standalone | `test_an_unknown_action_is_observable_and_refused_on_qt_as_on_anywidget`; known-product-event tests | `test_qt_delivers_one_message_at_a_time_and_waits_for_it_to_be_handled`; `test_a_load_waits_for_the_structure_and_not_merely_for_the_message` | `test_qt_view_channel_close_only_detaches_its_own_event_sink`; `test_qt_payload_refs_replace_across_two_real_generations` |

Observed validation after the implementation was believed complete:

| Gate | Result |
|---|---:|
| `python -m pytest --receptor=llm -n 12 tests/` | 1295 passed, 3 environmental skips, exit 0 |
| `npm run test:js` | 271 passed, exit 0 |
| `npx tsc --noEmit` | exit 0 |
| `npm run build:runtime` | exit 0 |
| `npm run test:perf` | exit 0; 95k unknown 0.20 ms, hide 0.20 ms; dynamic 0.000693 ms/frame |
| `npm run test:e2e` | 30/30 suites, real Chromium/WebGL2, exit 0 |
| `python devtools/benchmarks/endpoint_isolation.py` | 95,000 atoms; host 0.0111 ms against the predeclared 100 ms threshold |

Mutation ledger:

| Mechanism | Mutation | Test that failed | Restored result |
|---|---|---|---|
| endpoint-lifetime generation identity after completion | remove the inactive popup manager when a generation completes | `test_live_molecular_reload_starts_independent_host_and_canvas_generations` | pass |
| endpoint-lifetime generation identity after fallback | remove the inactive popup manager after JSON fallback | `test_a_popup_targeted_stream_fallback_cancels_and_loads_the_same_endpoint` | pass |

Not done in this slice: no change to completion-wait timeout semantics, no
frontend-orchestrator decomposition, no structure windowing and no dependency
pinning. The only remaining closure action is independent audit. The developer
scratch notebook was not used as evidence or included in the implementation.

### Phase 6 — Ownership audit and limited consolidation

1. Record an ownership table for every mutable transfer, projection and endpoint
   lifecycle state introduced or touched by Phases 2-5.
2. Confirm that the Python transfer manager and static projector created by
   those phases are their single owners; remove duplicate compatibility state
   only where tests prove parity.
3. Extract validated runtime dispatch only if a concrete duplicate owner or
   correctness guard still remains in `core.py`.
4. Do not perform a general decomposition of `index.ts`,
   `viewer-controller.ts` or unrelated frontend orchestration before 1.0. Record
   that work as post-1.0 unless a named mutable state still has multiple owners.
5. Keep behavior changes out of extraction-only commits.

**Exit:** the ownership table has exactly one owner for each listed mutable
state; structural checks find no direct transfer transition in `core.py` and no
duplicate static-export authority; every removed compatibility path has a
parity test. No prediction about hypothetical future edits is used as evidence.

#### Phase 6 implementation evidence — 2026-08-08

The durable ownership table is
[`../transport_state_ownership.md`](../transport_state_ownership.md). The audit
confirmed that `StructureTransferManager` is already the sole transfer-state
authority and `PopupSnapshotMixin` is already the sole canonical/static
projector. No extraction of runtime dispatch or frontend orchestrators was
therefore justified.

One concrete duplicate lifecycle representation did remain: `core.py` kept
popup manager, popup mode, deferred messages and flush reentrancy in four
parallel containers. `EndpointTransferRegistry` now owns one
`EndpointTransferState` bundle per destination. `MolSysView` coordinates wire
effects through that registry and no longer has to register or remove the same
endpoint from several dictionaries.

Observed validation:

| Gate | Result |
|---|---:|
| focused transfer/ordering/lifecycle/projector set | 66 passed, exit 0 |
| `python -m pytest --receptor=llm -n 12 tests/` | 1298 passed, 3 environmental skips, exit 0 |
| frontend gates | not run; no TypeScript or runtime source changed |

Mutation ledger:

| Mechanism | Mutation | Test that failed | Restored result |
|---|---|---|---|
| endpoint-close isolation | make `close(endpoint)` clear every popup bundle | `test_closing_one_endpoint_removes_its_complete_bundle_only` | pass |
| endpoint single ownership | reintroduce `_popup_endpoint_modes` in `core.py` | `test_core_has_no_parallel_endpoint_lifecycle_containers` | pass |
| static-projector single authority | add a second `_build_static_export_snapshot` in `export.py` | `test_static_export_snapshot_has_one_constructor` | pass |

Not done: no behavior change to the transfer protocol, no TypeScript movement,
no general `core.py` decomposition and no compatibility alias for the removed
private dictionaries. Phase 6 needs independent audit before closure.

### Phase 7 — Missing seam evidence

Close the companion smoke inventory:

- re-run the full E2E and performance suites after the rework and compare them
  with the Phase 0 baseline;
- `camera_stranded_inside_scene` tests at the complete seam: inside/outside
  browser detection, manifest wrapping, Python catalog delivery and payload;
- popup-size wiring test that stubs `window.open` and asserts the computed width
  in the actual features string, not only the size helper;
- Qt S8 evidence against the Qt bridge's own ordered queue: a molecular load
  must precede following scene operations without depending on the AnyWidget
  `_binary_structure_stream`;
- real-window Qt validation after S9 and representation changes: load a
  structure, change the whole representation, verify that framing contains the
  system and that wheel zoom can move outward;
- static HTML visual validation of initial framing and a subsequent
  representation change; `test_build_html_state.py` alone is state evidence,
  not render evidence;
- panel-popup System hierarchy refresh after loading a second structure;
- load-reload-hide/show smoke after `clearGlobalRepresentations`, with a clean
  console. Keep the existing real-Mol\* E2E and add the human smoke rather than
  claiming the automated test is absent;
- an exactly-once readiness/reconnect regression for the chosen Phase 4b
  closure: canonical projection if migrated, or bounded replay plus explicit
  summary resend if deferred;
- wire-serialization coverage for NumPy scalars, quantities and optional
  box/time.
- audit standalone E2E failure cleanup: a failed assertion must close Chromium
  in `finally` or terminate immediately. Remove remaining `process.exitCode = 1`
  paths that can leave a live browser and turn a real failure into a timeout.

**Exit:** each claim that depends on composition has at least one complete-seam
test, not only destination-level units.

### Phase 8 — Representative performance and memory gate

Use both structural axes. At minimum:

| Atoms | Structures |
|---:|---:|
| 2,000 | 1, 10, 100 |
| 20,000 | 1, 10, 100 |
| 100,000 | 1, 10, 100 |
| 300,000+ | 1 and a feasible multi-structure case |

Include a scientifically plausible solvated macromolecule, not only repeated
small peptides or pathological synthetic coordinates. Measure:

- MolSysViewer serialization time;
- first visible structure and total load time;
- peak and retained Python RSS;
- browser JS, native and GPU memory where available;
- structure change/frame latency;
- popup bootstrap and host responsiveness;
- representation replacement peak;
- Qt payload assembly peak;
- close/dispose retained growth.
- scene-history memory at 25 snapshots for ordinary and large literal-overlay
  scenes;
- built artifact size, cold import and cold/warm first-view construction.

External MolSysMT conversion time is reported separately and, when actionable,
filed in `../molsysmt`; it is not hidden inside a MolSysViewer number.

**Exit:** every result is compared with the Phase 0 predeclared threshold and
noise band; no regression exceeds its threshold without an explicit waiver;
every claimed improvement has an A/B measurement.

### Phase 9 — Documentation and upstream closure

1. Make the retained architecture records pass this closed assertion list:
   `data_plane_architecture.md` no longer describes R2/D3/D4 as future work or
   Qt as JSON-only; `runtime_message_router.md` no longer describes
   `PopupReplayLog`, JSON canvas bootstrap or D4b as the active interactive
   architecture; `scene_contracts.md` no longer labels implemented Contract S9
   as implementation-pending; Qt docs distinguish payload-scheme binary
   transport from AnyWidget `buffers=` without calling Qt non-binary.
2. Verify rather than rewrite already-correct indexes: the pending-proposals
   README must continue to identify the master plan as current and R2/D3/D4 as
   closed. Reconcile `roadmap.md` and `path_to_1_0.md` against that same state.
3. Update `checkpoints.md` with the smoke round, Contracts S8/S9 and the camera
   authority caution; update any maintained session handoff record that still
   points before the round.
4. Close stale pending bug/proposal entries. In particular mark the
   `clearGlobalRepresentations` item complete with `34755fb9` and remove the
   obsolete "Interim" guidance from the completed System hierarchy proposal.
5. Confirm that the MolSysMT deep-copy report remains represented by its
   resolved upstream archive; do not recreate it as open work unless new
   evidence differs from that resolution.
6. File the prepared Mol\* empty-scene camera-bounds report and record its URL.
7. Record the final architecture and honest limitations in durable developer
   docs.

**Exit:** each closed assertion above is checked directly, stale phrases have
zero hits outside explicitly historical sections, and entrypoint documents
agree about what is implemented, manually validated and post-1.0.

### Phase 10 — Product and release gates

1. Close and record compatible versions/channels for the UIBCDF dependency
   stack (`argdigest`, `depdigest`, `smonitor`, MolSysMT and related packages).
2. Build the release wheel and conda artifacts and test installation from
   supported channels in fresh environments.
3. Reverify the Phase 0 dependency-name and package-resource contract against
   those release artifacts; this is where resolver/version compatibility becomes
   a blocking assertion.
4. Verify runtime resources (`viewer.js`, `runtime_actions.json`) from an
   installed artifact, not the source checkout.
5. Verify the one-line first-contact path.
6. Decide whether thin `save_state(path)` / `load_state(path)` helpers are needed;
   do not imply a portable molecular session bundle unless one is designed.
7. Decide hover telemetry semantics.
8. Add notebook execution to CI or record an explicit release waiver.
9. Complete scientific dogfooding on representative laboratory workflows.
10. Run the final smoke matrix and release-version consistency checks.

**Exit:** no open pre-1.0 gate remains in `path_to_1_0.md`.

---

## 9. Mandatory tests and mutation ledger

Every phase reports ordinary tests and mutations separately. Mutate guards and
state-transition protections, not every line that produces functionality.

Mutation entries are ordered after their mechanism is connected end to end. In
particular, the camera-diagnostic mutation is not meaningful until Z2 is fixed
and the signal can cross the manifest-governed browser-to-Python seam.

If a mutation leaves its intended test green, the first hypothesis is that the
mutation hit the wrong layer or an inactive build artifact, not that the test is
good. Prove that the mutated code path executed before interpreting the result;
only then decide whether the test itself is hollow.

Minimum mutation cases:

| Mechanism | Mutation | Expected failure |
|---|---|---|
| targeted cancellation | remove destination from cancel | popup fallback regression |
| browser action declaration | remove `camera_stranded_inside_scene` from `actions` | S9 delivery/manifest test |
| popup action declaration | remove `molsysviewer-sync-hierarchy` from `popup_actions` | hierarchy refresh/manifest test |
| manifest guard | add an undeclared statically emitted action on either seam | transversal manifest test |
| Qt unknown-action guard | restore forwarding after diagnostic | Qt authority-boundary test |
| terminal release | skip retained-buffer release | lifecycle/memory assertion |
| generation guard | accept stale ack | stale-generation test |
| lazy fallback | construct portable JSON eagerly | zero-build binary-success test |
| session boundary | accept old `session_id` | reconstruction E2E |
| S8 | flush scene before structure completion | ordering test/E2E |
| canonical export | rebuild from journal | interaction-count invariance test |
| canonical readiness (if selected in 4b) | replay `_message_history` on `ready` | reconnect invariance test |
| add-on projection (if a hook is required) | drop one registered contribution | shipped/fake add-on projection test |
| optional metadata | invent box or time | payload fidelity test |
| camera diagnostic | disable inside-scene report | camera diagnostic test |
| popup size consumption | ignore computed panel width in `window.open` | popup host wiring test |
| Qt S8 ordering | deliver a scene op before the queued Qt molecular load | Qt bridge ordering test |

For each mechanism, the report records:

```text
mechanism:
mutation:
test:
mutated result: FAIL
restored result: PASS
```

Use `cp` or a patch to restore mutations, never destructive Git commands that
could remove concurrent work.

---

## 10. Validation commands

Follow `AGENTS.md` test discipline: focused tests first; the full Python suite
once after the implementation is believed correct. Agents may use 12 workers
and `pytest-receptor`:

```bash
pytest --receptor=llm -n 12 tests/test_relevant_file.py -x
pytest --receptor=llm -n 12 tests/
```

Frontend closure when TypeScript changes:

```bash
cd molsysviewer/js
npm run test:js
npx tsc --noEmit
npm run build:runtime
npm run test:perf
npm run test:e2e
```

E2E runs require a real browser and WebGL2. They do not pass by skipping browser
launch. Qt real-window checks require the supported display/GPU environment.

Never edit or inspect `molsysviewer/viewer.js` or its map manually. Rebuild the
runtime only after the final TypeScript source edit.

---

## 11. Performance acceptance

The rework is not accepted merely because correctness tests pass.

- Unknown-message and ordinary interaction toll must not materially regress
  from the recorded sub-millisecond baseline.
- A successful binary load performs zero portable-JSON builds and product
  Python performs zero ViewerJSON conversions.
- Historical ViewerJSON timings are context, not acceptance values: profiler
  overhead and the upstream MolSysMT deep-copy fix changed their meaning. Repeat
  current wall-clock A/B measurements on the pinned dependency version before
  claiming a magnitude.
- Snapshot/export size is invariant to irrelevant interaction count.
- If Phase 4b selects canonical live bootstrap, ready/reconnect delivery is
  invariant to irrelevant interaction count. If it selects contained deferral,
  the retained journal's byte/item bound is measured and enforced instead.
- Terminal transfer cleanup leaves no retained growth proportional to completed
  or cancelled transfers.
- Scene-history retained memory is measured at its configured limit; if literal
  overlay payloads make 25 snapshots unsafe, add a byte budget or structural
  sharing rather than silently lowering scientific fidelity.
- Host interaction during popup bootstrap is measured; if it remains serialized,
  the observed delay must be accepted explicitly.
- Qt peak memory is reported separately from retained memory.
- No claim of 60 FPS or large-system readiness is made without a fixture and
  measured frame distribution.

Use thresholds derived from the Phase 0 baseline and record any deliberate
tradeoff. Do not invent universal budgets before measuring the target hardware.

---

## 12. Change and landing discipline

- One phase or independently auditable slice per commit.
- Audit the working tree before commit when possible.
- Never include `sandbox/` notebooks in implementation commits.
- Never combine generated runtime output with unrelated source changes.
- Preserve user changes in a dirty worktree.
- Reports state exactly what was not done.
- A phase closes only after its acceptance criteria, mutation evidence and
  required suites have been independently checked.

No big-bang branch may replace the runtime only at the end. The old path is
removed in the same slice that proves the replacement, not retained indefinitely
as a hidden compatibility fork.

---

## 13. Definition of complete

This plan is complete when:

1. all currently identified correctness and distribution defects are closed;
2. transfer lifecycle is typed, endpoint-aware and generation-safe;
3. JSON fallback is lazy on every negotiated binary path;
4. popup and static export both derive from canonical current state;
5. embedded readiness/reconnect either derives from canonical current state or
   has an explicit, measured and enforced bounded-journal waiver;
6. shipped add-on behavior survives static export, while any unsupported
   arbitrary add-on state is documented honestly; a public extension contract
   exists only if a real pre-1.0 consumer requires it;
7. no unbounded journal is an accidental scene authority;
8. transport, projection and endpoint lifecycle state have explicit single
   owners, without requiring a broad frontend file decomposition;
9. widget reconstruction, popup closure, Qt, static HTML and real Mol\* seams
   have direct evidence;
10. representative atom/structure measurements show no material regression and
   document remaining limits;
11. the built artifacts contain their runtime manifest and have honest dependency
    metadata;
12. every statically emitted action on both governed seams is pinned to the
    correct manifest and direction/category by a transversal guard;
13. developer documents agree with shipped behavior;
14. installation, onboarding, dogfooding and release checks are closed or have
    an explicit owner-approved waiver;
15. post-1.0 scope remains deferred rather than leaking into this rework.

The intended result is not merely fewer bugs. It is a runtime whose performance
and correctness follow from explicit ownership and bounded state, and whose next
scientific domains can grow without reopening transport, authority or export
semantics.
