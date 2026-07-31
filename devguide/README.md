# Developer guide

`devguide/` contains the repository's engineering contracts, current planning,
implementation references, and explicitly deferred work. It is not a changelog:
Git and `docs/content/developer/changes_notes.md` already preserve chronology.

## Read first

Use these documents in this order:

1. [`scene_contracts.md`](scene_contracts.md) is normative for scene state,
   regions, whole, color ownership, ordering, persistence, and scene objects.
2. [`engineering_rules.md`](engineering_rules.md) defines implementation and
   verification rules.
3. [`session_reproducibility.md`](session_reproducibility.md) applies whenever
   user-created state is introduced.
4. [`architecture.md`](architecture.md) and
   [`digestion_and_dependencies.md`](digestion_and_dependencies.md) describe the
   Python/TypeScript boundary and the supporting UIBCDF tooling.
5. [`checkpoints.md`](checkpoints.md) is the current handoff. It must stay short
   and must not accumulate history.

When documents disagree, the contracts and current code win over plans, vision
documents, and historical audits.

## Current status and planning

- [`checkpoints.md`](checkpoints.md): current repository handoff.
- [`path_to_1_0.md`](path_to_1_0.md): release gate toward `1.0.0`.
- [`roadmap.md`](roadmap.md): current execution priorities.
- [`pending_bugs/`](pending_bugs/): confirmed unresolved defects.
- [`pending_proposals/`](pending_proposals/): active proposals, with its own
  indexed status table.
- [`pending_proposals/post_1.0/`](pending_proposals/post_1.0/): explicitly
  deferred work.

An implemented design does not remain under `pending_proposals/`. Implementation
plans are removed once their durable contracts and public documentation exist;
Git retains the plan.

## Durable engineering references

### Runtime and protocol

- [`architecture.md`](architecture.md)
- [`units_and_quantities.md`](units_and_quantities.md)
- [`js_runtime_build_and_version_sync.md`](js_runtime_build_and_version_sync.md)
- [`load_modes_and_append_structures_status.md`](load_modes_and_append_structures_status.md)
- [`python_js_boundary_audit_2026_07.md`](audits/python_js_boundary_audit_2026_07.md)
- [`pytest_receptor.md`](pytest_receptor.md)
- [`smonitor.md`](smonitor.md)

### Interaction and scene semantics

- [`interaction_overview.md`](interaction_overview.md)
- [`interaction_targets_and_selection.md`](interaction_targets_and_selection.md)
- [`interaction_gestures_and_menus.md`](interaction_gestures_and_menus.md)
- [`interaction_modifiers_and_future.md`](interaction_modifiers_and_future.md)
- [`interaction_verified_state.md`](interaction_verified_state.md)
- [`selections.md`](selections.md)
- [`annotations.md`](annotations.md)
- [`strips.md`](strips.md)
- [`molstar_color_strings.md`](molstar_color_strings.md)

### Product surfaces

- [`canvas_minimal_ux.md`](canvas_minimal_ux.md)
- [`image_export_direction.md`](image_export_direction.md)
- [`addon_panel_widget_contract.md`](addon_panel_widget_contract.md)
- [`molsyssuite_addon_direction.md`](molsyssuite_addon_direction.md)
- [`smoke_test.md`](smoke_test.md)
- [`benchmarks/README.md`](benchmarks/README.md)

### Performance baselines

Measured evidence, not estimates. Each records the command that reproduces it.

- [`performance/trajectory_transport_baseline_2026_07.md`](performance/trajectory_transport_baseline_2026_07.md)
  — AnyWidget trajectory transport.
- [`performance/qt_transport_baseline_2026_07.md`](performance/qt_transport_baseline_2026_07.md)
  — Qt standalone transport; why binary needs no new channel.
- [`performance/message_path_regression_check_2026_07.md`](performance/message_path_regression_check_2026_07.md)
  — the post-envelope message-path baseline required by
  [`engineering_rules.md`](engineering_rules.md) §6.

### Standalone

- [`standalone_direction.md`](standalone_direction.md)
- [`standalone_host_plan.md`](standalone_host_plan.md)
- [`standalone_supported_environment.md`](standalone_supported_environment.md)
- [`standalone_packaging_strategy.md`](standalone_packaging_strategy.md)
- [`standalone_qt_ci_and_gl_decisions.md`](standalone_qt_ci_and_gl_decisions.md)
- [`standalone_performance_and_depythonization.md`](standalone_performance_and_depythonization.md)
- [`standalone_v2_evolution_plan.md`](standalone_v2_evolution_plan.md)

Closed Qt investigations live under [`audits/`](audits/README.md). The two
remaining product defects are tracked in
[`pending_bugs/standalone_qt_live_demo_reload.md`](pending_bugs/standalone_qt_live_demo_reload.md)
and [`pending_bugs/post_1.0/`](pending_bugs/post_1.0/README.md).

## Project direction

These documents explain product intent, not current implementation status:

- [`guiding_principles.md`](guiding_principles.md)
- [`development_mantra.md`](development_mantra.md)
- [`v1_vision_and_styles.md`](v1_vision_and_styles.md)
- [`scene_look_styles_direction.md`](scene_look_styles_direction.md)
- [`style_battery_and_future_ideas.md`](style_battery_and_future_ideas.md)
- [`molsysmovie_vision.md`](molsysmovie_vision.md)
- [`render_quality_vision.md`](render_quality_vision.md)
- [`future_vision_beyond_1_0.md`](future_vision_beyond_1_0.md)
- [`areas_of_opportunity_analysis.md`](areas_of_opportunity_analysis.md)

## Course material

Course planning is isolated under [`course/`](course/):

- [`course/introduction.md`](course/introduction.md)
- [`course/common_core.md`](course/common_core.md)
- [`course/structure.md`](course/structure.md)

Course plans are not API references. Every example must still be checked against
the current public API before execution.

## Historical implementation records

[`archive/`](archive/README.md) contains completed implementation plans retained
only when their rationale remains useful. They are not current instructions.
Closed audits are stored separately in [`audits/`](audits/README.md).

## Maintenance rules

- Do not append historical sessions to `checkpoints.md`.
- Do not copy normative clauses into plans; link to the contract.
- Every proposal declares one of: `proposed`, `approved`, `blocked`,
  `post-1.0`, or `implemented`.
- `implemented` documents are promoted to a durable reference or removed from
  `pending_proposals/`.
- Performance claims without a reproducible benchmark are labeled estimates.
- A document naming current code or APIs must be checked against the repository,
  not against an earlier plan.
