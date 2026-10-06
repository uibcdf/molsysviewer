# Archived implementation plans

- [`welcome_card_flashes_during_system_rebuild.md`](welcome_card_flashes_during_system_rebuild.md) — #164: explicit pending-load state prevents transient Welcome during rebuilding; DOM insertion guard, empty/failure controls and 39 core browser suites pass.
- [`automatic_source_regions_corrupt_unicode_labels.md`](automatic_source_regions_corrupt_unicode_labels.md) — #165: source regions preserve Unicode labels and deterministic duplicate suffixes; batch/progressive identity, session guards and actual Studio card checks pass.

- [`amber_test_environments_missing_openmm.md`](amber_test_environments_missing_openmm.md) — #163: provision the AMBER backend in all scientific test/development recipes; the real complementary-file workflow and full exact-source suites pass on Linux, macOS and Windows.

- [`scientific_test_environments_missing_rdkit.md`](scientific_test_environments_missing_rdkit.md) — #161: provision RDKit for real chemical fixtures in all test/development recipes; the guard rejects three omissions and the native source-pair matrices collect their scientific cases.

- [`interactions_materialization_guard_shared_wrapper.md`](interactions_materialization_guard_shared_wrapper.md) — #162: profile the concrete serializer rather than shared decorators; a real serialization control and the 22-case scene module verify the bounded large-frame guard.

- [`compound_interaction_projection_dispatches_per_group.md`](compound_interaction_projection_dispatches_per_group.md) — #141: bounded public geometry batches preserve projection semantics and cut the measured 1,000-observation preparation to 281–291 ms; real-call guards and the complete Interactions browser suite pass.

- [`source_pair_ci_for_direct_main_pushes.md`](source_pair_ci_for_direct_main_pushes.md) — #137: direct-main Python 3.14 validation, preserving manual frozen-candidate identity checks; three native source-pair jobs pass.
- [`source_pair_provider_pin_below_runtime_floor.md`](source_pair_provider_pin_below_runtime_floor.md) — #138: exact released MolSysMT 0.22.4 replaces the obsolete provider below the runtime floor; installed audits and native/scientific suites pass.
- [`dependency_inventory_paths_are_not_portable.md`](dependency_inventory_paths_are_not_portable.md) — #139: portable relative inventory keys prevent false Windows drift; native Windows full-suite qualification passes.

These documents describe completed implementation work whose rationale may still
be useful. They are historical records, not current instructions or API
references. Current behavior is defined by code, tests, durable contracts, and
user/developer documentation.

- [`styles_first_slice.md`](styles_first_slice.md)
- [`styles_second_slice_and_project_config.md`](styles_second_slice_and_project_config.md)
- [`elastnetmt_addon_plan.md`](elastnetmt_addon_plan.md)
- [`molsysmovie_plan.md`](molsysmovie_plan.md)
- [`standalone_qt_prototype_plan.md`](standalone_qt_prototype_plan.md)
- [`canvas_panel_transition.md`](canvas_panel_transition.md)
- [`canvas_panel_taxonomy_2026_04.md`](canvas_panel_taxonomy_2026_04.md)
  — the two-panel `Navigate` / `Workbench` model MolSysViewer did **not** build; Studio
  and its ten subpanels shipped instead. Kept for the map-vs-inventory distinction and
  the navigator alternatives, not for its layout.
- [`digest_every_public_callable.md`](digest_every_public_callable.md)
  — gate 9, done 2026-08-12: 448 public callables digested, 0 undigested, 29 exempt with
  a stated reason, 0 argument names without a digester. Read for the finding rather than
  the plan: decorating surfaced more defects than it introduced, and the 29 exemptions are
  why the gate could reach zero honestly.
- [`migrate_the_standardizer_to_alias_tables.md`](migrate_the_standardizer_to_alias_tables.md)
  — the imperative standardizer became declared `AliasTable`s. Read for the finding
  rather than the plan: the code it replaced tested a caller string nothing produces, so
  it had never renamed anything, and `view.get(element='group', index=True)` raised.
- [`standalone_performance_and_depythonization.md`](standalone_performance_and_depythonization.md)
  — **its premise is dead.** It argues from Numba JIT cold-start latency and MolSysMT is
  now Rust. The de-pythonization argument may survive; the latency figures do not. Do not
  plan from it without re-measuring.

Resolved defect reports, kept for their evidence:

- [`interactions_query_dock_cannot_stage.md`](interactions_query_dock_cannot_stage.md) — #158, correlated successful Studio queries activate the public selection owner before staging A/B; stale replies do not.
- [`interactions_display_filter_changes_calculation.md`](interactions_display_filter_changes_calculation.md) — #159, calculation atom scope is explicit and independent of display A/B; the real browser guards 20 calculated observations and one drawn occurrence.

- [`extracted_interaction_repeated_structures.md`](extracted_interaction_repeated_structures.md)
  — #156, repeated-structure extraction retains every interaction display destination, the first current-frame copy, source maps and session restoration.
- [`attribute_scalar_colors_unit_contract.md`](attribute_scalar_colors_unit_contract.md)
  — #98, scalar coloring retains physical units and requires compatible explicit ranges across Python and canvas paths.
- [`review_python_ecosystem_policy_adoption.md`](review_python_ecosystem_policy_adoption.md)
  — #110, support-library boundaries and published developer-tool integration are adopted with scoped source and hosted evidence.

- [`emitted_smonitor_codes_lack_templates.md`](emitted_smonitor_codes_lack_templates.md)
  — #107, all 48 diagnostic codes have templates; real emission passes five profiles, and the guard now catches missing messages.
- [`public_api_reference_stale_entries_and_cold_imports.md`](public_api_reference_stale_entries_and_cold_imports.md)
  — #117, cold scene imports and the public reference resolve; strict Sphinx and the full canonical Python suite pass.
- [`python_pocket_blob_rejects_documented_multi_iso_options.md`](python_pocket_blob_rejects_documented_multi_iso_options.md)
  — the public Python multi-iso call reached `main` and the 0.23.4 release;
  its public-manager guard and notebook execution passed.
- [`hosted_ci_has_never_passed.md`](hosted_ci_has_never_passed.md)
  — the public MolSysMT/Viewer pair removed the solver barrier; hosted CI 7/7,
  core E2E 34/34 and documentation notebooks then passed on `main`.
- [`public_noarch_promotion_succeeds_but_final_verifier_exits_one.md`](public_noarch_promotion_succeeds_but_final_verifier_exits_one.md)
  — an exact public file can now be checked through a rerunnable read-only workflow;
  verification never repeats a successful promotion.
- [`python_wheel_can_ship_a_stale_viewer_runtime.md`](python_wheel_can_ship_a_stale_viewer_runtime.md)
  — the 0.23.4 wheel preflight now checks its Python metadata and compiled JS
  runtime together before Conda rebuilds the bundle.
- [`npm_publisher_runs_twice_for_one_version.md`](npm_publisher_runs_twice_for_one_version.md)
  — the 0.23.4 tag published npm successfully, then the GitHub Release
  redundantly tried the immutable version again; tag push is now the sole
  automatic npm trigger.
- [`docs_lite_views_pinned_to_unpublished_npm_version.md`](docs_lite_views_pinned_to_unpublished_npm_version.md)
- [`standalone_export_mutates_live_widget_state.md`](standalone_export_mutates_live_widget_state.md)
- [`tight_initial_camera_framing_for_exported_views.md`](tight_initial_camera_framing_for_exported_views.md)
  — closed without a change: the framing was measured and found correct.
- [`dark_light_theme_synchronization_and_transparent_canvas.md`](dark_light_theme_synchronization_and_transparent_canvas.md)
  — delivered as `export.html(background=...)`; the adopter chose `"transparent"`.
- [`camera_zoom_out_blocked_after_scene_replay.md`](camera_zoom_out_blocked_after_scene_replay.md)
  — Contract S9. Fixed. The accepted upstream report is preserved in
  [`report_molstar_empty_scene_camera_bounds.md`](report_molstar_empty_scene_camera_bounds.md).
- [`unbounded_alias_dependencies_can_break_import.md`](unbounded_alias_dependencies_can_break_import.md)
  — an unbounded `argdigest` / `molsysmt` pair could make `import molsysviewer` fail
  outright. Closed by version floors held together as one contract; the alias source is
  now MolSysMT's public provider.

Completed work, kept for the reasoning:

- [`full_pr_ci_can_be_skipped_and_direct_push_debt_is_unchecked.md`](full_pr_ci_can_be_skipped_and_direct_push_debt_is_unchecked.md)
  — #116, full PR gates and administrator-preserving branch protection verified; actual nightly CI and core E2E recovery execute successfully.

- [`audit_dependency_floors_and_source_pins.md`](audit_dependency_floors_and_source_pins.md)
  — #106, read-only canonical dependency audit covers recipes, environments and controlled source installs before packaging and CI consumers.
- [`recheck_latest_conda_forge_qt_before_1_0.md`](recheck_latest_conda_forge_qt_before_1_0.md)
  — superseded by the 2026-09-28 scope decision: Qt-host certification is
  deferred to [#113](https://github.com/uibcdf/molsysviewer/issues/113), outside
  the core 1.0 gate.

- [`first_read_comprehension_gaps_2026_08.md`](first_read_comprehension_gaps_2026_08.md)
  — the README quick start now leads with an executable reproducibility loop;
  the first-read findings and positioning decision closed in #40.
- [`embedding_views_in_external_documentation.md`](embedding_views_in_external_documentation.md)
  — how a third party publishes views on their own website. Every step closed;
  the port to MolSysMT was done by MolSysMT.
- [`molsysmt_embedding_feedback_and_transparent_adapter_pattern.md`](molsysmt_embedding_feedback_and_transparent_adapter_pattern.md)
  and [`molsysmt_adoption_response_2026_08.md`](molsysmt_adoption_response_2026_08.md)
  — the first external adopter's report and our reply.
- [`system_panel_hierarchy_summary.md`](system_panel_hierarchy_summary.md)
- [`lazy_json_fallback_payload.md`](lazy_json_fallback_payload.md)
  — implemented, validated and measured; only its header said otherwise.
- [`zero_copy_visual_rendering.md`](zero_copy_visual_rendering.md)
  — pre-D4 feasibility analysis superseded by the implemented data plane and
  the measured post-1.0 performance strategy.
- [`whole_representation_succession_semantics.md`](whole_representation_succession_semantics.md)
  — audited: the whole's representation succeeds, it never accumulates. The rule
  is now Contract S10.
- [`scene_object_owner_field.md`](scene_object_owner_field.md)
  — creator attribution: `view.attributed_to(owner)` records what made an object and
  never restricts what the user may do to it.
- [`opt_in_hover_telemetry.md`](opt_in_hover_telemetry.md)
  — hover transport is off until something listens, and `hover_target` reports
  `telemetry_disabled` rather than a plausible empty target.
- [`exported_page_self_declaration.md`](exported_page_self_declaration.md)
  — an exported page declares the version that produced its scene, and the Studio says
  when there is no Python behind it.
- [`documentation_execution_in_ci.md`](documentation_execution_in_ci.md)
  — done 2026-08-06. Read for the correction: the trigger is a change in the library, not
  in the notebooks, so the workflow runs with `--force` and consults no run mark.
- [`import_state_replays_region_indices_instead_of_its_recipe.md`](import_state_replays_region_indices_instead_of_its_recipe.md)
  — a region is its recipe (Contract R), but import restored the atoms the recipe had
  selected on the *other* system. Read for what was refuted: refusing an import when the
  atom counts differ is both too strict and too weak.
- [`focus_overlay_survives_a_save_only_if_named.md`](focus_overlay_survives_a_save_only_if_named.md)
  — one pattern was answering two questions: does the user manage this region, and does it
  outlive the operation that made it. Read for why splitting a predicate beat loosening it.
- [`what_save_state_promises.md`](what_save_state_promises.md)
  — the proposal that became #38's four slices. Read for the five open decisions and what
  each was answered with: notably that binding a state to its structure meant re-resolving
  onto a different one, not refusing it.
- [`bioassembly_copies_lose_their_chain_hierarchy.md`](bioassembly_copies_lose_their_chain_hierarchy.md)
  — 60 copies of a capsid drew their waters and one protein. Read for what was refuted:
  there was no per-chain ceiling, and contiguity does not save a repeated label —
  Mol* groups by the value it finds.
- [`exported_view_background_not_transparent_when_loaded_dark.md`](exported_view_background_not_transparent_when_loaded_dark.md)
  — a transparent view showed white on a dark page. Read for the elimination: six
  mechanisms refuted by measurement, and the one that mattered was outside both documents —
  a missing `color-scheme` letting the browser's white base canvas show through.
- [`reuse_attribute_availability_within_one_scene_summary_synchronization.md`](reuse_attribute_availability_within_one_scene_summary_synchronization.md)
  — one synchronization asked the molecular system twice for the same attribute inventory;
  removing the second traversal took `regions.add` from 46.6 ms to 26.8 ms. Read for why
  the value is passed rather than cached.
- [`camera_focus_on_object_and_the_units_of_its_arguments.md`](camera_focus_on_object_and_the_units_of_its_arguments.md)
  — a public camera method that raised with its own default. Read for how one argument name
  came to carry three readings of its unit, and why the tempting fix would have hidden the
  factor of ten instead of removing it.
- [`capability_audit_advertises_removed_methods.md`](capability_audit_advertises_removed_methods.md)
  — the generated capability audit named three public methods that the 0.22 simplification
  had removed. Read for why a guard asking "does this prefix match anything" passes for the
  worst of the three: `view.get` was absorbing ten unrelated `view.get_*` event accessors
  into a row attributed to MolSysMT, inflating it from 7 public callables to 17.
- [`xdist_controller_aborts_under_twelve_workers.md`](xdist_controller_aborts_under_twelve_workers.md)
  — half of all `-n 12` runs died with `KeyError: <WorkerController gwN>`. Read for the two
  wrong turns: the warning classes were rejected correctly in the first pass and the real
  cause was the *import* that looking one up triggers, and three clean plain runs almost
  produced a false report against our own pytest plugin.
- [`evidence_a_stable_capability_has_not_earned.md`](evidence_a_stable_capability_has_not_earned.md)
  — four capabilities declared an evidence level nothing had observed. Read for the
  criterion that was unmet without being visible: the reason two of them deserved `stable`
  was written in the generator's source, where a reader of the generated audit never meets
  it.
- [`headless_chrome_hangs_on_any_exported_page.md`](headless_chrome_hangs_on_any_exported_page.md)
  — **withdrawn, not resolved**: the browser on that machine still will not navigate to
  `http://` from the command line, and nothing here can reach it. Read for the two
  refuted passes rather than the outcome. The first blamed disk pressure with sound
  reasoning and never checked it against the 5.1 MB Chrome actually writes; the second
  established what the defect is — the server records no request at all — without
  establishing why CDP-driven navigation to the same URL takes 0.2 s.
- [`consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md`](consolidate_quantity_digesters_on_pyunitwizard_canonical_paths.md)
  — the `[L]` consolidation, done in `a785b1bf`. Read for the audit at the end: the wider
  scope it declared — box, time, energy, dimensionless vectors — came to nothing a
  migration could fix, and the assumption it had flagged as an assumption did not hold.
  What was live went to [#86](https://github.com/uibcdf/molsysviewer/issues/86).
- [`duration_lets_pint_errors_out_of_the_public_api.md`](duration_lets_pint_errors_out_of_the_public_api.md)
  — pint's `UndefinedUnitError` reaching callers of twelve public methods. Read for what
  filing one leak found: `"250"` was parsing as 250 **radians** and `True` as one
  millisecond, and the fix was a shared boundary taking a dimensionality rather than a
  patch on one digester.

- [`adopt_resumable_zenodo_verification.md`](adopt_resumable_zenodo_verification.md)
  — the pinned common provider now supplies exact-tag and scheduled complete discovery, with truthful delayed states and a publication-anchored deadline.

## Final design review — 2026-09-30

- [partial_coordinate_edits_leave_derived_state_stale.md](partial_coordinate_edits_leave_derived_state_stale.md) — #118: Coordinate edits validate their complete atom/frame batch before mutation, invalidate named scientific interaction coverage only on edited structures, clear dependent caches/history and refresh the lazy molecular projection.
- [view_transformations_lose_scene_state.md](view_transformations_lose_scene_state.md) — #119: Copy, extraction and merge now share canonical scene-state transfer.
- [stale_scene_handles_mutate_replacements.md](stale_scene_handles_mutate_replacements.md) — #120: Handles are checked against the exact registered object lifetime before mutation and history staging.
- [scene_queries_expose_mutable_records.md](scene_queries_expose_mutable_records.md) — #121: Scene records now detach nested data for Shapes, Annotations, Measurements and Selections.
- [dict_mutations_bypass_scene_lifecycle.md](dict_mutations_bypass_scene_lifecycle.md) — #122: Region and layer managers retain dictionary reads but reject assignment, deletion, update, pop, popitem, setdefault and in-place union.
- [rejected_scene_operations_erase_redo.md](rejected_scene_operations_erase_redo.md) — #123: History stages a pre-operation snapshot and commits it only after a successful scene mutation.
- [global_scene_inspection_omits_interactions.md](global_scene_inspection_omits_interactions.md) — #124: Global scene summary and dictionary/dataframe/styler inspection now include typed Interactions rows, their named-analysis reference, layer and effective visibility.
- [public_entrypoints_lack_uniform_digestion.md](public_entrypoints_lack_uniform_digestion.md) — #125: Annotation creation is implemented only as view.annotations.add with the full named signature; add_annotation is removed.

## Public persistence — 2026-10-01

- [session_scene_rejection_replaces_destination.md](session_scene_rejection_replaces_destination.md) — #127: Invalid session scenes are restored on an isolated view before replacing an existing destination; rejection preserves open work and closes temporary widgets without copying the incoming trajectory.

## Public HTML export — 2026-10-01

- [noninline_html_exports_omit_scene.md](noninline_html_exports_omit_scene.md) — #128: Shared non-inline HTML exports retain the canonical scene in a versioned sidecar with an escaped URL, ownership protection and validated browser loading.
- [exported_html_reports_ready_before_scene_restoration.md](exported_html_reports_ready_before_scene_restoration.md) — #129: HTML readiness follows successful complete scene restoration and a new Mol* draw; failed restoration exposes an error.
- [exported_html_omits_studio_summaries.md](exported_html_omits_studio_summaries.md) — #130: Static export includes the authoritative Studio summaries without duplicate scene operations, preserving valid controls and the running-session explanation.

## Installed test imports — 2026-10-01

- [installed_tests_cannot_import_edit_helpers.md](installed_tests_cannot_import_edit_helpers.md) — #131: Package-qualified edit helpers and conftest imports support isolated installed-wheel collection and ordinary development collection; the guard rejects restored bare imports.

## Release gate evidence — 2026-10-01

- [release_gate_conflates_staging_evidence_with_strict_1_0_requirements.md](release_gate_conflates_staging_evidence_with_strict_1_0_requirements.md) — #103: Candidate-bound staging, public installed-pair and hosted core E2E checks independently verify runs, immutable files and environment artifacts; pre-1.0 exceptions remain nonzero and cannot clear 1.0.
- [conda_promotion_gate_omits_current_matrix_and_windows.md](conda_promotion_gate_omits_current_matrix_and_windows.md) — #134: Exact-file promotion requires current four-platform pair coverage and a successful Windows launcher run bound to the candidate commit, version, build and SHA-256.
- [adopt_shared_public_conda_verifier.md](adopt_shared_public_conda_verifier.md) — #133: Both workflows call the pinned shared public verifier and retain independent evidence; its hosted call passes, local candidate/promotion tools remain compatible, and the Windows launcher defect stays tracked under #101.

- [dependency_audit_mistakes_evidence_actions_for_source_checkouts.md](dependency_audit_mistakes_evidence_actions_for_source_checkouts.md) — #136: evidence-action repository inputs no longer become source checkouts; undeclared and duplicate actual checkouts remain rejected.

## Scientific loading follow-up — 2026-10-04

- [mixed_partial_hierarchy_load_breaks_scene_state.md](mixed_partial_hierarchy_load_breaks_scene_state.md) — #157: Detached load candidates validate public scene identity before commit; rejected malformed or mixed partial-hierarchy systems preserve the existing scene, sources, history and analyses.
