# Transport and popup audit follow-ups

**Status:** audit record, swept 2026-08-06 and closed out the same day — **items 1 to 8 are all done or measured**, each marked in its own title. **Items 1 to 9 are all done, measured or verified.** What remains is 10 to 12, which are standing boundaries rather than work. Its execution order is superseded by
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md).

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

## P0 — ~~Correctness defect~~ — resolved

### 1. ~~Address fallback cancellation to the popup endpoint~~ — RESOLVED

`_transmit_binary_structure_chunk` addresses the chunk's own
`target_endpoint_id`, so a cancel can no longer reach the wrong endpoint.
Pinned in `tests/test_structure_stream_ordering.py`.

### 2. ~~Test widget reconstruction and kernel-session replacement end to end~~ — DONE

Covered end to end by `js/tests/e2e/endpoint-lifecycle.e2e.ts`, including
the kernel-session replacement path.

### 3. ~~State the D3 timeout semantics precisely and evaluate event-loop expiry~~ — DONE

Stated in `data_plane_architecture.md` under *D3 implemented*, together with
the reason there is no timer thread.

### 4. ~~Add seam-level tests when behavior depends on composition~~ — DONE as a standing rule

Codified as a standing rule in `engineering_rules.md` (integration seams),
rather than closed as a one-off task.

### 5. ~~Reconcile the retained R2/D3/D4 design records with the shipped state~~ — DONE

Both contradictions fixed. `data_plane_architecture.md` and
`runtime_message_router.md` were also promoted out of `pending_proposals/`
on 2026-08-05, since a dozen documents cite them as current.

### 6. ~~Build the JSON fallback lazily~~ — DONE and measured

Implemented and measured: **32 ms against 1,459 ms**. The producer is
`_new_lazy_molecular_projection` in `viewer/core.py`; the proposal is in
[`../archive/lazy_json_fallback_payload.md`](../archive/lazy_json_fallback_payload.md).

### 7. ~~Measure endpoint-global scene deferral during popup bootstrap~~ — CLOSED 2026-08-06

**0.0097 ms** host projection latency against a 100 ms threshold fixed
before running, with the popup stream deliberately in flight. Recorded in
[`../performance/qt_payload_copies_and_endpoint_isolation_2026_08.md`](../performance/qt_payload_copies_and_endpoint_isolation_2026_08.md).

### 8. ~~Measure copies and peak memory in the Qt binary scheme~~ — MEASURED 2026-08-06, path kept

The join peaks at **2x the payload** at every size measured. The path is
kept deliberately, with the trigger that would change it written down, in
[`../performance/qt_payload_copies_and_endpoint_isolation_2026_08.md`](../performance/qt_payload_copies_and_endpoint_isolation_2026_08.md).

### 9. ~~Retire the probe-induced Qt unknown-action asymmetry~~ — DONE, verified 2026-08-06

The premise was stale: the probe is a declared test-only action and Qt
already refuses an unknown action without forwarding it. Mutation-verified
in `tests/test_qt_transport_contract.py`.

### 10. ~~Decide the public persistence convenience separately from persistence~~ — DONE

`export_state()` / `import_state()` version 2 already provide tested overlay
state persistence. They do not bundle the molecular system and require a
compatible structure to be loaded first.

The decision is to provide `save_state(path)` / `load_state(path)` as atomic
UTF-8 JSON conveniences around that existing contract. Their public docs state
that the molecular system, camera and undo history are excluded and that a
compatible structure must be loaded first. No `.msv` extension or portable
session bundle is introduced. Such a bundle still needs its own format,
versioning, provenance and compatibility policy and remains post-1.0.

The persistence slice was independently mutation-audited and closed on
2026-08-09; see
[`../audits/pre_1_0_phases_5_6_8_9_10_audit_2026_08.md`](../audits/pre_1_0_phases_5_6_8_9_10_audit_2026_08.md).

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
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md),
which begins with the broken distribution artifact and a green complete
baseline, then closes the active transport/manifest defects and transversal
guards before architectural rework. This document remains the evidence and
acceptance-detail record for its delegated items.
