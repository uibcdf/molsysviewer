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
