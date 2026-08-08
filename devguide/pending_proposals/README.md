# Pending proposals

Only unresolved designs belong here. Implemented plans are promoted to durable
documentation or removed; Git retains their development history.

**Nothing in this directory is finished work.** `data_plane_architecture.md` and
`runtime_message_router.md` used to sit here as the design record for the
envelope, the shared manifest and the array-native layout; they were promoted to
`devguide/` on 2026-08-05 and are normative now. Structure windowing,
compression, workers, shared memory and multiview remain post-1.0.

## Open before 1.0

- [`what_needs_a_human_2026_08.md`](what_needs_a_human_2026_08.md): **read this
  one first.** Seven items that no amount of work here can close — a Qt
  validation that needs a real screen, a fix nobody has reviewed, two decisions,
  a handover to MolSysMT, an upstream answer, and Phase 5's own opening. As of
  2026-08-06 everything outside Phase 5 that did not need a person is done.
- [`digest_every_public_callable.md`](digest_every_public_callable.md): the release
  owner's rule that every public callable carries `@digest`. Measured: 515 public
  callables are undecorated against 286 decorated, and 482 raw `ValueError`/`TypeError`/
  `KeyError` never reach the diagnostics catalogue. The cost is not the decorator but
  declaring the arguments each function introduces, so the job must be sized by argument
  names rather than by function count.
- [`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md):
  canonical execution plan for the corrections, transport/export rework,
  architectural extraction, seam hardening, representative performance work
  and release gates required before 1.0. The audit documents below remain its
  evidence, not competing execution plans.
- [`transport_popup_audit_followups_2026_08.md`](transport_popup_audit_followups_2026_08.md)
  and [`open_items_after_the_2026_08_smoke_round.md`](open_items_after_the_2026_08_smoke_round.md):
  the two audit inventories. **Items 1–9, and sixteen of nineteen, are closed.**
  What remains in either is collected in `what_needs_a_human_2026_08.md`. Closed
  items keep one line and a pointer, so neither reads as a work queue any more.
- [`molsysmt_docs_pipeline_analysis.md`](molsysmt_docs_pipeline_analysis.md):
  their pipeline read at the scale it is about to reach. The scheme is piloted in
  one notebook; 138 call `msm.view()` and 26 carry a target. The structural
  finding is that the code a reader sees and the code that produced the picture
  are two different files with nothing checking they agree, and the proposed
  direction is to let the tutorial cell generate its own view.
- [`classic_script_runtime_for_offline_bundles.md`](classic_script_runtime_for_offline_bundles.md):
  **not to be implemented yet.** Building the runtime as a classic script instead
  of ESM, which would let many shared views open from a disk with no server. The
  research and the browser measurements are done and recorded; the trigger is a
  real user with that need.
- [`first_read_comprehension_gaps_2026_08.md`](first_read_comprehension_gaps_2026_08.md):
  **five of six findings acted on**; what is left is one positioning decision,
  what the README leads with. Kept for its evidence — what one uninterrupted
  first read concluded wrongly, and which document caused each wrong turn. A
  maintainer cannot produce this about their own project.
- [`opt_in_hover_telemetry.md`](opt_in_hover_telemetry.md): stop forwarding hover
  to the kernel when nobody is listening. The July round deduplicated identical
  hovers, which fixes a resting mouse and not a moving one. **Blocked on one
  product decision** — what `view.hover_target` means when telemetry is off.
*(A JIT cold-start proposal was drafted here on 2026-07-31 and withdrawn the same
day: MolSysMT no longer uses Numba. See
[`../standalone_performance_and_depythonization.md`](../archive/standalone_performance_and_depythonization.md).)*

## Deferred until after 1.0

See [`post_1.0/`](post_1.0/). It contains:

- the approved Interactions domain and Studio design;
- configurable canvas picking granularity;
- lazy structure sources and partial materialization;
- multiview synchronization;
- advanced annotation, representation, and chemical-metadata work;
- typing-generation and test-output studies;
- deeper large-system rendering analysis;
- [`qt_popout_parity.md`](post_1.0/qt_popout_parity.md): the Qt shell is built
  with `include_popout=False`, so the entire popup control plane — manifest
  validation, canonical snapshot, endpoint identity — is exercised only on
  AnyWidget. Staged at Stage 4 of the host plan, not a defect;
- [`scene_object_owner_field.md`](post_1.0/scene_object_owner_field.md): an
  add-on's shape is indistinguishable from one the user drew;
- [`qt_render_check_on_a_gpu_runner.md`](post_1.0/qt_render_check_on_a_gpu_runner.md):
  the render gate is closed on real GPU; what is missing is a machine that proves
  it again automatically;
- [`proteinview_external_review_and_ideas.md`](post_1.0/proteinview_external_review_and_ideas.md):
  an idea inventory drawn from reading an external terminal viewer. It is not a
  design. Its first section records which of the ideas it raises are **already**
  covered by approved documents here, so read it before opening a proposal about
  interactions, pockets, or agent integration;
- [`viewing_in_the_terminal.md`](post_1.0/viewing_in_the_terminal.md): show the
  scene as pixels in a terminal, from the existing CLI and from Python. The
  headless pixel source and the CLI argument parsing already exist, so this is
  one new component plus two triggers. It also records an unbounded dimension
  argument in today's image export that it does not own.

These remain useful, but they expand product scope or require benchmark and
upstream decisions. They do not block the current release.

## Practical decision

- **Done:** the router inventory/AnyWidget seam and the array-native serializer,
  negotiated buffer delivery, chunking, acknowledgement, cancellation, JSON
  fallback, and embedded-canvas E2E are implemented.
- **Now:** execute the staged pre-1.0 rework and hardening master plan. R2, D3
  and D4 remain closed as contracts; their transfer implementation is being
  replaced where the audit demonstrated weak state ownership.
- **Preserve 1.0 semantics:** all selected structures remain materialized in
  `view.molsys`; binary is a transport choice, not a new scientific model.
- **Session lifecycle:** kernel restart or widget reconstruction creates a new
  attachment. Old popups are closed or disconnected and never adopt a new
  `session_id` implicitly; a replacement popup authenticates and bootstraps
  from current state.
- **First after 1.0:** implement the Interactions domain by vertical slices,
  with state/history/API before Studio UI.
- **Opportunistic small work:** configurable canvas picking may be scheduled
  independently once the post-1.0 API freeze opens.
- **Wait for dependencies:** chemical metadata waits for MolSysMT's schema;
  advanced MVS annotations and rendering tiers wait for their Mol*/product
  trigger.

## Triage rules

- `approved` means the design may be implemented; it does not make it a release
  gate.
- A proposal that depends on a benchmark records the benchmark command and
  fixture before implementation.
- Performance reports separate both structural axes: atom count and structure
  count.
- Overlapping proposals name one canonical owner for each concern.
- Once implemented, remove the document from this directory.
- A UI companion cannot start before its Python domain, protocol, state, and
  history contracts exist.
- Post-1.0 location is a scope decision, not an implicit commitment to
  implement every document.
