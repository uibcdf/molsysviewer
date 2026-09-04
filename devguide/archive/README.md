# Archived implementation plans

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
