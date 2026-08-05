# Pending proposals

Only unresolved designs belong here. Implemented plans are promoted to durable
documentation or removed; Git retains their development history.

## Implemented, retained as the design record


They preserve the 1.0 scientific model: `view.molsys` remains a complete selected
`molsysmt.MolSys`. The data-plane work removed avoidable
`ViewerJSON`/nested-list/text-JSON amplification without introducing partial
residency.

*These two are a deliberate exception to the triage rule "once implemented,
remove the document from this directory."* They are the only written account of
**why** the envelope, the shared manifest and the array-native layout are shaped
the way they are, several documents link to them by path, and the decisions they
record are still load-bearing. Read them as history, not as pending work. If they
are ever moved, the links in `roadmap.md`, `checkpoints.md` and this file move
with them.

Structure windowing, eager/windowed modes, compression, workers, shared memory,
BroadcastChannel, and multiview remain post-1.0. Camera acquisition/movie export
is also explicitly post-1.0.

## Open before 1.0

- [`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md):
  canonical execution plan for the corrections, transport/export rework,
  architectural extraction, seam hardening, representative performance work
  and release gates required before 1.0. The audit documents below remain its
  evidence, not competing execution plans.
- [`transport_popup_audit_followups_2026_08.md`](transport_popup_audit_followups_2026_08.md):
  focused follow-up from the post-R2/D3/D4 audit. It records one targeted-stream
  cancellation defect, missing lifecycle evidence, documentation drift, the
  lazy-fallback priority, and measured improvement candidates without reopening
  the completed architecture. Read it together with
  [`open_items_after_the_2026_08_smoke_round.md`](open_items_after_the_2026_08_smoke_round.md);
  the union of both is the complete current audit inventory.
- [`documentation_execution_in_ci.md`](documentation_execution_in_ci.md): run
  `docs/execute_notebooks.py` in CI. Sphinx does not execute notebooks, which is
  how ten broken ones survived unnoticed. Postponed by decision, not closed.
- [`lazy_json_fallback_payload.md`](lazy_json_fallback_payload.md): the
  array-native path avoids *sending* the JSON payload but not *building* it, so
  every load pays the ViewerJSON path (~10× the binary one) and discards it. The
  fallback is sound; paying for it eagerly is not.
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
  what one uninterrupted first read of this repository concluded wrongly, with
  the document that caused each wrong turn and the artifact that disproved it.
  Two findings are README-facing and affect prospective users; four are
  contributor-facing. Perishable evidence — a maintainer cannot produce it about
  their own project.
- [`whole_representation_succession_semantics.md`](whole_representation_succession_semantics.md):
  audit only. `areas_of_opportunity_analysis.md` §2 records the whole's global
  representation as deliberately **additive**; the runtime reads as **replace**
  (add-then-remove) and the Python model is single-valued. No test pins either,
  and `scene_contracts.md` is silent. Decide which is true, then make the
  normative document say it.
- [`opt_in_hover_telemetry.md`](opt_in_hover_telemetry.md): stop forwarding hover
  to the kernel when nobody is listening. The July round deduplicated identical
  hovers, which fixes a resting mouse and not a moving one. **Blocked on one
  product decision** — what `view.hover_target` means when telemetry is off.
*(A JIT cold-start proposal was drafted here on 2026-07-31 and withdrawn the same
day: MolSysMT no longer uses Numba. See
[`../standalone_performance_and_depythonization.md`](../standalone_performance_and_depythonization.md).)*

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
