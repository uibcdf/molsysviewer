# Pending proposals

Every entry is filed and closed under [`../reporting_protocol.md`](../reporting_protocol.md):
it carries front matter and is tracked by a GitHub issue. **Only single-theme proposals
live here** — plans and inventories are not queue entries and sit elsewhere in the
devguide.

Only unresolved designs belong here. Implemented plans are promoted to durable
documentation or removed; Git retains their development history.

**Nothing in this directory is finished work.** `data_plane_architecture.md` and
`runtime_message_router.md` used to sit here as the design record for the
envelope, the shared manifest and the array-native layout; they were promoted to
`devguide/` on 2026-08-05 and are normative now. Structure windowing,
compression, workers, shared memory and multiview remain post-1.0.

## Open before 1.0

- [`consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md`](consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md):
  classify legacy physical-magnitude digesters and consolidate compatible paths on the
  existing `ensure_quantity()` helper, adding explicit canonical branches only where
  representative interactive benchmarks justify them.
- [`reuse_attribute_availability_within_one_scene_summary_synchronization.md`](reuse_attribute_availability_within_one_scene_summary_synchronization.md):
  operation-local reuse of the MolSysMT attribute inventory while synchronizing region
  and whole summaries. The re-audit behind uibcdf/molsysmt#147 measured 510 adapter
  queries but only 229 unique pairs and a controlled median reduction from 46.71 ms to
  26.62 ms. This is independent of MolSysMT's 1.0 gate.
- [`what_save_state_promises.md`](what_save_state_promises.md): what a saved state
  actually restores, raised from outside to keep the paper's reproducibility claim exact.
  The exclusions are already deliberate; what is missing is a stated boundary between
  semantic scene state, visual state, molecular data and a portable session. One obstacle
  is structural rather than unimplemented: **the camera is the frontend's state mirrored
  back**, so it cannot simply become another key.
- [`addon_maturity_and_ownership.md`](addon_maturity_and_ownership.md): the ownership half
  is documented and done; what remains is whether maturity belongs to the host contract.
  Measured: four MolSysSuite add-ons declare four different things about themselves in an
  untyped `meta` dict, `AddonSpec` has no `status` field, and only MolSysMT is discovered
  on install.
- [`molsysmt_docs_pipeline_analysis.md`](molsysmt_docs_pipeline_analysis.md):
  their pipeline read at the scale it is about to reach. The scheme is piloted in
  one notebook; 138 call `msm.view()` and 26 carry a target. The structural
  finding is that the code a reader sees and the code that produced the picture
  are two different files with nothing checking they agree, and the proposed
  direction is to let the tutorial cell generate its own view.
- [`molsysmt_known_source_form_and_large_string_detection.md`](molsysmt_known_source_form_and_large_string_detection.md):
  upstream proposal motivated by a 95,000-atom PDB string. It combines bounded,
  content-aware `get_form()` detection with a public explicit source-form hint for
  callers that know their input representation by construction. MolSysViewer keeps
  only a temporary benchmark-level direct converter import until MolSysMT exposes the
  public path.
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
*(A JIT cold-start proposal was drafted here on 2026-07-31 and withdrawn the same
day: MolSysMT no longer uses Numba. See
[`../standalone_performance_and_depythonization.md`](../archive/standalone_performance_and_depythonization.md).)*

## Not in this queue

Three documents used to be listed here and are not queue entries: they are a plan and two
inventories, and **one theme, one issue** cannot apply to them.

- [`../what_needs_a_human_2026_08.md`](../what_needs_a_human_2026_08.md) — **read this one
  first.** Three observations or decisions that no work here can close.
- [`../pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md)
  — the canonical execution plan and its phase dashboard.
- [`../audits/transport_popup_audit_followups_2026_08.md`](../audits/transport_popup_audit_followups_2026_08.md)
  and [`../audits/open_items_after_the_2026_08_smoke_round.md`](../audits/open_items_after_the_2026_08_smoke_round.md)
  — the two audit inventories, almost entirely closed.

## Deferred until after 1.0

See [`post_1.0/`](post_1.0/). It contains:

- the approved Interactions domain and Studio design;
- configurable canvas picking granularity;
- lazy structure sources and partial materialization;
- multiview synchronization;
- advanced annotation, representation, and chemical-metadata work;
- typing-generation and test-output studies;
- deeper large-system rendering analysis;
- [`post_1.0/representative_scale_followups.md`](post_1.0/representative_scale_followups.md):
  Phase 8's measured next optimizations — typed/dictionary topology transport,
  bounded profiling-driven structure prefetch, and the Qt lower-copy trigger;
- [`qt_popout_parity.md`](post_1.0/qt_popout_parity.md): the Qt shell is built
  with `include_popout=False`, so the entire popup control plane — manifest
  validation, canonical snapshot, endpoint identity — is exercised only on
  AnyWidget. Staged at Stage 4 of the host plan, not a defect;
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
- **Now:** finish Phase 10 of the staged pre-1.0 rework and hardening master
  plan, plus Phase 7's two visible Qt observations. R2, D3, D4 and Phases 0a-6,
  8 and 9 remain closed and audited.
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
