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

Resolved defect reports, kept for their evidence:

- [`docs_lite_views_pinned_to_unpublished_npm_version.md`](docs_lite_views_pinned_to_unpublished_npm_version.md)
- [`standalone_export_mutates_live_widget_state.md`](standalone_export_mutates_live_widget_state.md)
- [`tight_initial_camera_framing_for_exported_views.md`](tight_initial_camera_framing_for_exported_views.md)
  — closed without a change: the framing was measured and found correct.
- [`dark_light_theme_synchronization_and_transparent_canvas.md`](dark_light_theme_synchronization_and_transparent_canvas.md)
  — delivered as `export.html(background=...)`; the adopter chose `"transparent"`.
- [`camera_zoom_out_blocked_after_scene_replay.md`](camera_zoom_out_blocked_after_scene_replay.md)
  — Contract S9. Fixed; only the upstream report to Mol\* is still open, and it
  has its own file.

Completed work, kept for the reasoning:

- [`embedding_views_in_external_documentation.md`](embedding_views_in_external_documentation.md)
  — how a third party publishes views on their own website. Every step closed;
  the port to MolSysMT was done by MolSysMT.
- [`molsysmt_embedding_feedback_and_transparent_adapter_pattern.md`](molsysmt_embedding_feedback_and_transparent_adapter_pattern.md)
  and [`molsysmt_adoption_response_2026_08.md`](molsysmt_adoption_response_2026_08.md)
  — the first external adopter's report and our reply.
- [`system_panel_hierarchy_summary.md`](system_panel_hierarchy_summary.md)
