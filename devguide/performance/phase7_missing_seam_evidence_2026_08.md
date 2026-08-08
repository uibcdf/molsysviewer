# Phase 7 missing-seam evidence - August 2026

## Status

The automated part of Phase 7 is implemented. Two required observations remain
human-owned and are not counted as passes:

- Qt framing and outward wheel zoom in a real visible GPU window;
- the manual load/reload/hide/show smoke recorded in
  `pending_proposals/what_needs_a_human_2026_08.md`.

## Closed seams

| Claim | Complete-seam evidence |
|---|---|
| S9 camera diagnostic | Browser inside/outside detection in `viewer-controller-message-refresh.test.ts`; live AnyWidget envelope in `widget-seam.e2e.ts`; Python identity, catalog and payload delivery in `test_runtime_seam_integration.py` |
| Popup window size | `panel-popup-welcome.e2e.ts` intercepts `window.open` and asserts the actual features string |
| Qt S8 ordering | `test_qt_transport_contract.py` proves the Qt bridge's own one-message queue waits for `structure_ready`, independently of AnyWidget transfer state |
| Static export framing | `exported-page-framing.e2e.ts` opens the generated file, reads Mol* camera/render state, changes the whole to `spacefill`, and checks usable framing again |
| Panel System hierarchy | `panel-popup-welcome.e2e.ts` drives the live AnyWidget `enqueueMessage` seam through two molecular projections and observes MET/ALA being replaced by GLY/SER in the panel relay |
| Load/reload visibility | `global-reprs-across-loads.e2e.ts` loads two structures, checks live representation refs, hides and shows the replacement, and requires an empty browser error channel |
| Ready/reconnect exactly once | `test_pending_message_flush.py` compares each handshake with the canonical snapshot and rejects identical duplicate projections |
| Wire serialization | `test_wire_serializable_messages.py` covers NumPy indices, quantity-based shape inputs, popup snapshots, and optional quantity-based box/time; loader tests separately pin absence rather than invention |
| Failed E2E cleanup | `test_e2e_reliability.py` rejects every remaining `process.exitCode = 1` catch path; all standalone suites terminate immediately on failure |

## Observed validation

- Python full suite before the final wire-only test addition: 1299 passed, 3
  documented environmental skips, exit 0. The final focused wire suite passed
  5/5.
- JavaScript: 271/271 passed.
- TypeScript: exit 0.
- Runtime build: exit 0.
- Shared real-browser runner: 30/30 suites, Chrome 149, WebGL2 through
  ANGLE/SwiftShader. The camera, reload and other final test-only extensions
  also passed in their focused real-browser suites.
- Performance: unknown message 0.30 ms, hide 0.50 ms, dynamic request gate
  0.00076 ms/frame, 9,500 hierarchy nodes. Every hard budget passed. The hide
  sample is above the historical ~0.1 ms comparison point; no improvement is
  claimed and Phase 8 must measure its representative distribution.

## Mutation ledger

```text
mechanism: E2E failures cannot leave Chromium alive behind process.exitCode
mutation : restore process.exitCode = 1 in hierarchy-interaction.e2e.ts
test     : test_e2e_failures_cannot_leave_chromium_alive_until_timeout
result   : FAIL with mutation / PASS after cp restore

mechanism: one ready handshake applies each identical current projection once
mutation : append a duplicate first message in _build_embedded_runtime_snapshot
test     : test_ready_projects_current_state_without_trait_reserialization
result   : FAIL with mutation / PASS after cp restore
```

## Not done

No Qt real-window/GPU observation and no human load/reload smoke were performed.
The phase cannot be reported closed until those observations are recorded or an
explicit waiver is approved.
