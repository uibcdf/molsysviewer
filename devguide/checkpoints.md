# Development checkpoint

This is the current handoff, not a changelog. Replace its contents when the
project state changes.

## Repository state

- Branch: `main`.
- Base commit: `7a14fbfc`.
- Latest release checkpoint: `0.20.0`.
- The working tree intentionally contains the uncommitted July 2026 devguide,
  performance, array-native transport, runtime-router, popup, Qt, and API
  cleanup round. Do not assume an untracked file is disposable.
- `sandbox/Smoke_Test.ipynb` is developer scratch state. Never include it in a
  product commit and do not use it as architectural evidence.
- Generated `molsysviewer/viewer.js` was rebuilt with
  `npm run build:runtime`; never edit or inspect it as source.

## Completed in the current round

### Devguide and pre-1.0 scope

- Historical, superseded, post-1.0, active proposal, bug, audit, and performance
  material was separated and indexed.
- Camera acquisition/movie export, structure windowing/lazy materialization,
  Interactions, configurable picking, and multiview remain post-1.0.
- Missing box and time remain valid scientific absence; no transport path
  invents them.

### Array-native materialized-structures data plane

- D0 baseline documents Python and browser amplification.
- D1 serializes topology once and structural arrays directly from
  `molsysmt.MolSys`, using contiguous little-endian `float32` coordinates in
  angstrom.
- D2 negotiates AnyWidget capability, validates typed descriptors and buffers,
  constructs Mol* structures without nested coordinate arrays, and retains the
  JSON compatibility/reproducibility path.
- D2b splits on the structures axis, allows one chunk in flight, requires begin
  and chunk acknowledgements, rejects stale/duplicate/malformed delivery, and
  releases or falls back observably on cancellation and connector failure.
- Box and time are aligned optional arrays and remain absent when absent in the
  source `MolSys`.
- Coordinates use the `structure-planar-c` layout (`[structures, 3, atoms]`) so
  Mol\* frames are zero-copy `subarray` views. The interleaved layout forced a
  per-frame de-interleaving pass — 930k scalar assignments and 15k allocations
  on the 5,000×62 case, 30M and a full second copy on 100×100,000 — for no gain
  on the Python side, where the transpose fuses into the contiguous `float32`
  conversion. Verified by a real-browser E2E.

### Runtime router and popup control plane

- R0 pure `RuntimeMessageRouter` validates viewer/session/source/target,
  endpoint roles, direction, malformed envelopes, targeted delivery, endpoint
  removal, and bounded duplicate-command state.
- R1 envelopes the AnyWidget seam. A shared manifest `runtime_actions.json`
  classifies every action for Python (`runtime_contract.py` +
  `viewer/runtime_router.py`) and TypeScript (`runtime-actions.ts` +
  `widget-envelope.ts`). Enveloping lives in `MolSysViewerWidget.send` (the
  connector owns the wire), so Qt stays raw and `initial_messages` /
  `_message_history` keep domain messages. `_handle_inbound_message` validates
  identity/direction/action↔payload coherence and deduplicates commands (a
  duplicate yields `command_duplicate_ack`, not a re-apply). Bootstrap source
  and binary buffers stay off the control-plane envelope.
- Popup channels use an unguessable token plus exact source, viewer, session,
  authority, host, and popup endpoint identity.
- Popup traffic now carries `RuntimeEnvelope`; host and popup both route it.
- Popup controls no longer apply a reproducible operation locally and then ask
  the host to apply it again.
- Closing/reopening/disposal revokes popup endpoints and stale channels.
- `PopupReplayLog` retains only the current molecular generation, coalesces
  current-state/high-frequency projections, and gives panel popups only an
  explicit UI projection allowlist. Panel bootstrap receives no molecular or
  structure-dependent visual operations.
- Camera synchronization is an endpoint event, not a Python projection.

## Validation observed

- Python full suite (after R1): `1009 passed`, `3 skipped`, `0 failed` via
  `pytest --receptor=llm tests/`. The 3 skips are pre-existing environment gates
  (X11/WebGL/Qt GPU), not R1.
- JavaScript unit suite: `255 passed`, `0 failed`.
- TypeScript: `npx tsc --noEmit`, exit `0`.
- Runtime build: `npm run build:runtime`, exit `0`; R1 confirmed in the bundle.
- E2E without skips: array-native (real-browser WebGL trajectory), popup-channel
  (authenticated `postMessage` round trip), and structure-data-relay (buffers
  reach the addressed popup byte for byte and its ack returns) all passed. The
  relay suite is registered in `e2e-runner.ts`, so CI runs it with the rest.

## Auto-mutation record for the latest slice

```text
mechanism: a new molecular load drops superseded popup generations
mutation : append the new load instead of replacing replay entries
test     : popup replay keeps only the current molecular generation
result   : FAILS with mutation / PASSES restored

mechanism: current-state popup projections are last-write-wins
mutation : disable the last-write-wins branch
test     : popup replay coalesces high-frequency current-state projections
result   : FAILS with mutation / PASSES restored

mechanism: panel bootstrap is an explicit UI-only allowlist
mutation : return every replay entry to the panel
test     : panel popup bootstrap contains only explicit UI projections
result   : FAILS with mutation / PASSES restored

mechanism: duplicate popup command is rejected by the runtime router
mutation : bypass host-side router dispatch
test     : popup host sends and accepts messages only on the bound popup channel
result   : FAILS with mutation / PASSES restored

mechanism: a popup cannot impersonate the authority/host endpoint
mutation : remove expected popup endpoint binding at host receive
test     : popup host sends and accepts messages only on the bound popup channel
result   : FAILS with mutation / PASSES restored

mechanism: the popup snapshot is built from live state, never the journal
mutation : append _message_history to the snapshot
test     : snapshot is byte-for-byte identical under history growth
result   : FAILS with mutation / PASSES restored

mechanism: the snapshot returns defensive copies
mutation : emit _current_molecular_projection by reference
test     : consumer cannot mutate internal state through the result
result   : FAILS with mutation / PASSES restored

mechanism: regions carry the indices materialized for the current frame
mutation : drop atom_indices from the region create message
test     : region create carries current materialized indices
result   : FAILS with mutation / PASSES restored

mechanism: hidden scene objects are reported hidden to the popup
mutation : stop emitting hide_layer for hidden scene objects
test     : a hidden object inside a hidden layer stays hidden
result   : FAILS with mutation / PASSES restored

mechanism: saved selections travel as real save_selection messages
mutation : re-label them with an invented add_saved_selection op
test     : a saved selection is projected as a real save_selection message
result   : FAILS with mutation / PASSES restored

mechanism: a stream whose acknowledgement never arrives expires
mutation : make the deadline never expire
test     : a stream whose ack never arrives releases its arrays and falls back
result   : FAILS with mutation / PASSES restored

mechanism: an expired stream releases its retained arrays explicitly
mutation : clear the stream without dropping payload and chunks
test     : a stream whose ack never arrives releases its arrays and falls back
result   : FAILS with mutation / PASSES restored

mechanism: the popup projector covers every live scene object
mutation : stop projecting shapes, as a new unwired kind would behave
test     : every live scene object appears in the canvas snapshot
result   : FAILS with mutation / PASSES restored

mechanism: sendTo delivers to one popup endpoint, never both
mutation : make sendTo fan out again, as send does
test     : a canvas bootstrap never reaches a panel popup
result   : FAILS with mutation / PASSES restored

mechanism: relayed binary buffers cross the postMessage seam intact
mutation : relay empty buffers of the same length
test     : structure-data-relay E2E byte comparison
result   : FAILS with mutation / PASSES restored

mechanism: the load path reads the real structure count
mutation : restore structures.get_n_structures(), which always raises
test     : a real load over a lowered budget warns
result   : FAILS with mutation / PASSES restored

mechanism: the Qt scheme handler serves binary as octet-stream
mutation : always reply application/json
test     : the scheme handler serves binary and json by id
result   : FAILS with mutation / PASSES restored

mechanism: Qt refuses buffers it cannot deliver
mutation : drop them silently, as before
test     : qt refuses buffers instead of dropping them
result   : FAILS with mutation / PASSES restored

mechanism: an unknown action is observable on Qt, not silent
mutation : stop reporting unknown frontend actions
test     : an unknown action is observable on qt as it is on anywidget
result   : FAILS with mutation / PASSES restored

mechanism: the widget seam rejects a projection from another session
mutation : remove the session check in the inbound adapter
test     : widget-seam E2E, in a real browser
result   : FAILS with mutation / PASSES restored
```

## Pre-1.0 scale guard

There was no guard of any kind on load size: a trajectory large enough to
exhaust the browser tab simply tried until something died. That absence, not the
absence of windowed residency, was the 1.0 defect — windowing changes what
`view.molsys` means and its failure mode is silently wrong science, so it stays
post-1.0. `_private/scale_budget.py` now warns with the measured size, the note
that a canvas popup doubles the renderer cost, and a concrete
`structure_indices=range(0, N, stride)` that fits. It warns and never refuses;
`molsysviewer.set_structure_scale_budget(bytes)` tunes it, `0` silences it.

Latent bug surfaced by wiring it: `load_from_molsysmt` called
`structures.get_n_structures()`, which does not exist. The call always raised
into a bare `except Exception`, so `n_structures` silently stayed `None` and was
only recovered later by counting the serialized payload. Fixed to the
`structures.n_structures` attribute; mutation-verified.

`SharedArrayBuffer` was reclassified from "post-1.0" to **blocked on external
preconditions**: the COOP/COEP headers belong to the notebook host, and Mol\*
reorders coordinate arrays in place, which makes sharing one buffer between two
instances unsafe. No work on our side unblocks it.

## Hot-path findings from the critical review (measured)

- Coordinates now ship planar so Mol\* frames are zero-copy views; see the data
  plane proposal. Biggest single win found, and it cost nothing in Python.
- Mol\* re-emits hover on every resolved pick without comparing `prevLoci`, so a
  resting mouse sent ~30 identical messages per second to Python. The host now
  deduplicates the Python-bound hover projection; local UI is unaffected.
- `messageId` uses a per-session counter instead of `uuid4` (~12x cheaper) on
  both Python paths, matching TypeScript.
- A compact second wire format for ephemeral events was rejected on measurement
  (+375 B per message, ~22 KB/s at 60/s) — not worth dual-shape validation.
- The one-chunk-in-flight window was measured and deliberately kept; see the data
  plane proposal for the numbers.

Earlier tests in the same dirty round also cover forged source/token/session,
stale reopen, disposal of both popups, no local-plus-forward double apply,
array descriptor validation, stream ordering, stale generation, cancellation,
and JSON fallback.

## Open work and exact resume order

1. **R1 AnyWidget/embedded canvas — DONE.** Envelopes on the AnyWidget seam,
   Python as sole authority, wrapping in `MolSysViewerWidget.send`, inbound
   dedup with `command_duplicate_ack`. Validated: full Python `1009 passed /
   3 skipped` (receptor), `255` JS, `tsc` `0`, `build:runtime`, array-native +
   popup-channel E2E without skips; guards mutation-verified.
2. **R2 canonical popup bootstrap — projector and wiring DONE; cleanup next.**
   `MolSysView.build_popup_scene_snapshot(mode, endpoint)`
   (`viewer/popup_snapshot.py`) builds the current scene from live state:
   pure with respect to history and transport, `_message_history` and
   `_build_export_messages()` off limits, strict `mode`, defensive copies,
   dynamic regions materialized at the current frame, camera excluded.
   Mutation-verified in `tests/test_popup_snapshot.py` (7) and
   `tests/test_popup_snapshot_fidelity.py` (8); inflating the journal with
   10,000 ops leaves the snapshot byte-for-byte identical.
   The seam is wired: on popup ready the host sends
   `request_popup_scene_snapshot`, Python answers through
   `_answer_popup_scene_snapshot` with a `correlated_projection`, and the host
   consumes it at the seam and bootstraps with the canonical messages. The
   host-local fields already in `molsysviewer-initial-sync` (camera, spin/swing,
   dark mode, autohide, viewer/controls/panel mode, ambient/split) serve as
   `endpointState`. `PopupReplayLog` survives only as a 5 s fallback.
   Both closed: the journal is gone from the interactive path (kept only in
   `bootDocsView`, where a static export has no Python to ask), and
   `build_context_items` is the pure half that lets the panel snapshot carry
   add-on context items.
   Treat `session_id` as immutable per attachment: kernel restart or
   widget reconstruction must close or visibly disconnect the old popup; it
   must reject the replacement session. A popup for the replacement widget
   authenticates afresh and receives the canonical snapshot.
3. **D3 completion — DONE.** Each stream carries a deadline (30 s, restarted on
   every accepted acknowledgement) evaluated on main-thread entry points only;
   there is no timer thread, because `widget.send` is unsafe off the kernel
   thread for AnyWidget. On expiry the retained arrays are released explicitly,
   `structure_data_cancel` is sent, and the recorded JSON load is delivered with
   a `RuntimeWarning`. The benchmark now separates `peak_rss_growth` from
   `retained_growth` (current RSS via `/proc/self/statm`), since `ru_maxrss`
   alone is monotonic and cannot show what was released. Audit finding: no
   unsafe cross-thread send existed — the only thread serves headless export and
   playback is frontend-driven; a regression test pins that the timeout path
   sends on the calling thread.
4. **D4 endpoint parity — D4a DONE, D4b next.**
   D4a: `PopupHostManager.sendTo` delivers to one endpoint. This fixed a real
   leak — `send` fans out, so with both popups open the canvas bootstrap (with
   its molecular projection) also reached the panel popup. Closing a popup now
   fires `onEndpointClosed` and cancels that endpoint's pending scene-snapshot
   requests. Mutation-verified.
   D4b DONE: the canvas popup receives a **typed** molecular generation. Python
   starts an endpoint-addressed stream when the popup asks for its snapshot, the
   snapshot then omits `load_molsys_payload`, the host relays chunks through
   `sendTo` instead of consuming them, and the popup assembles with its own
   receiver and acknowledges back through the host. `enable_popout` no longer
   forces the JSON path. Host retention was rejected on memory grounds: it would
   have cost a permanent spare copy (120 MB on 100 x 100,000 atoms) even with no
   popup open, whereas relaying holds one chunk transiently. The remaining 2x
   browser memory (two Mol* instances) is inherent to two renderers;
   `SharedArrayBuffer` is the only real answer and needs cross-origin isolation,
   so it stays post-1.0. Qt binary transport requires its own benchmark and is
   not implied by AnyWidget success.
5. Re-run focused tests after each fix, then exactly one full JS and one full
   Python suite for the final implementation task. Use `pytest-receptor` for
   agent-facing Python output.

## Resume cautions

- Read `devguide/pending_proposals/runtime_message_router.md` and
  `devguide/pending_proposals/data_plane_architecture.md` first.
- The popup host and popup runtime already share envelope semantics; do not
  reintroduce `{type, data, from}` routing.
- Python remains the only authority for reproducible scene state.
- Never make an existing popup silently adopt a changed `session_id`.
  Continuity across kernel restart requires a new authenticated attachment and
  a fresh current-state projection.
- Binary buffers are runtime data, never scene history.
- A compact replay journal is not the same as a canonical state snapshot; keep
  that distinction explicit.
- Do not run E2E with `E2E_ALLOW_SKIP=1` when validating popup or rendering
  behavior.
- Never include `sandbox/Smoke_Test.ipynb` in commits.
