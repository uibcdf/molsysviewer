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

## The queue

Entries are rendered from each proposal's front matter — edit the proposals, not this
list. Deferred entries also carry the `post-1.0` milestone on the issue board.

<!-- generated: devguide_index -->

### Partially done (3)

- [`addon_maturity_and_ownership.md`](addon_maturity_and_ownership.md) — [#37](https://github.com/uibcdf/molsysviewer/issues/37) — Add-ons declare four different things about their own maturity, in an untyped dict. *(measured)*
- [`consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md`](consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md) — [#33](https://github.com/uibcdf/molsysviewer/issues/33) — Consolidate quantity digesters on PyUnitWizard canonical paths. *(inspected)*
- [`first_read_comprehension_gaps_2026_08.md`](first_read_comprehension_gaps_2026_08.md) — [#40](https://github.com/uibcdf/molsysviewer/issues/40) — What one uninterrupted first read of the project concluded wrongly, and which document caused each wrong turn. *(reproduced)*

### Blocked (1)

- [`molsysmt_known_source_form_and_large_string_detection.md`](molsysmt_known_source_form_and_large_string_detection.md) — [#42](https://github.com/uibcdf/molsysviewer/issues/42) — A large in-memory molecular string enters unbounded filename extension detection. *(measured)* — waiting on uibcdf/molsysmt#151

### Open (6)

- [`classic_script_runtime_for_offline_bundles.md`](classic_script_runtime_for_offline_bundles.md) — [#39](https://github.com/uibcdf/molsysviewer/issues/39) — Build the runtime as a classic script so many shared views open from a disk with no server. *(measured)*
- [`duplicated_infrastructure_across_the_ecosystem.md`](duplicated_infrastructure_across_the_ecosystem.md) — [#70](https://github.com/uibcdf/molsysviewer/issues/70) — Duplicated infrastructure across the MolSysSuite repositories keeps costing the same defect twice. *(measured)*
- [`evidence_a_stable_capability_has_not_earned.md`](evidence_a_stable_capability_has_not_earned.md) — [#65](https://github.com/uibcdf/molsysviewer/issues/65) — Four capabilities declare an evidence level nothing has observed, and the release gate cannot tell. *(measured)*
- [`evidence_labels_beyond_the_capability_audit.md`](evidence_labels_beyond_the_capability_audit.md) — [#61](https://github.com/uibcdf/molsysviewer/issues/61) — Decide whether the evidence labels govern the whole devguide or only the capability audit. *(measured)*
- [`molsysmt_docs_pipeline_analysis.md`](molsysmt_docs_pipeline_analysis.md) — [#41](https://github.com/uibcdf/molsysviewer/issues/41) — MolSysMT's documentation pipeline read at the scale it is about to reach. *(measured)*
- [`removing_the_viewers_own_get.md`](removing_the_viewers_own_get.md) — [#71](https://github.com/uibcdf/molsysviewer/issues/71) — Evaluate removing the viewer's own get(), now that msm.get(view) works. *(measured)*

### Deferred until after 1.0 (17)

- [`agent_token_cost_of_non_pytest_tests.md`](post_1.0/agent_token_cost_of_non_pytest_tests.md) — [#43](https://github.com/uibcdf/molsysviewer/issues/43) — Study the token cost of non-pytest test output for agent consumers.
- [`annotations_mvs_machinery.md`](post_1.0/annotations_mvs_machinery.md) — [#44](https://github.com/uibcdf/molsysviewer/issues/44) — Advanced annotations on Mol*'s MVS machinery.
- [`canvas_picking_level.md`](post_1.0/canvas_picking_level.md) — [#45](https://github.com/uibcdf/molsysviewer/issues/45) — Configurable canvas picking granularity via the context menu.
- [`chemical_metadata_loss_sdf_pdb.md`](post_1.0/chemical_metadata_loss_sdf_pdb.md) — [#46](https://github.com/uibcdf/molsysviewer/issues/46) — Preserve enriched chemical metadata from SDF and MOL2.
- [`export_rework_rough_edges.md`](post_1.0/export_rework_rough_edges.md) — [#47](https://github.com/uibcdf/molsysviewer/issues/47) — Rough edges of the 2026-08 export rework, to review cold.
- [`interactions_domain.md`](post_1.0/interactions_domain.md) — [#48](https://github.com/uibcdf/molsysviewer/issues/48) — An Interactions domain for derived atom-atom relations.
- [`multiview_split_screen.md`](post_1.0/multiview_split_screen.md) — [#49](https://github.com/uibcdf/molsysviewer/issues/49) — Multi-view split-screen viewport synchronization.
- [`proteinview_external_review_and_ideas.md`](post_1.0/proteinview_external_review_and_ideas.md) — [#50](https://github.com/uibcdf/molsysviewer/issues/50) — Idea inventory from an external terminal viewer.
- [`qt_popout_parity.md`](post_1.0/qt_popout_parity.md) — [#51](https://github.com/uibcdf/molsysviewer/issues/51) — Popout parity in the Qt standalone host.
- [`qt_render_check_on_a_gpu_runner.md`](post_1.0/qt_render_check_on_a_gpu_runner.md) — [#52](https://github.com/uibcdf/molsysviewer/issues/52) — Automate the Qt render check on a GPU runner.
- [`receiver_side_structure_barrier.md`](post_1.0/receiver_side_structure_barrier.md) — [#53](https://github.com/uibcdf/molsysviewer/issues/53) — Move the structure barrier to the receiver.
- [`representative_scale_followups.md`](post_1.0/representative_scale_followups.md) — [#54](https://github.com/uibcdf/molsysviewer/issues/54) — Post-1.0 performance architecture.
- [`structure_windowing_and_lazy_materialization.md`](post_1.0/structure_windowing_and_lazy_materialization.md) — [#55](https://github.com/uibcdf/molsysviewer/issues/55) — Structure windowing and lazy materialization.
- [`studio_interactions_subpanel_ui_design.md`](post_1.0/studio_interactions_subpanel_ui_design.md) — [#56](https://github.com/uibcdf/molsysviewer/issues/56) — Studio subpanel for Interactions.
- [`viewer_mixin_contract_and_caller_resolution.md`](post_1.0/viewer_mixin_contract_and_caller_resolution.md) — [#57](https://github.com/uibcdf/molsysviewer/issues/57) — Generated typing contract for MolSysView mixins.
- [`viewing_in_the_terminal.md`](post_1.0/viewing_in_the_terminal.md) — [#58](https://github.com/uibcdf/molsysviewer/issues/58) — View a scene as pixels in a terminal.
- [`visualization_representations_roadmap.md`](post_1.0/visualization_representations_roadmap.md) — [#59](https://github.com/uibcdf/molsysviewer/issues/59) — Advanced representations for pockets, voids, channels and interfaces.

<!-- /generated -->

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
