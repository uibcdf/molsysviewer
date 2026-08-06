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

- [`data_plane_architecture.md`](data_plane_architecture.md) — how structural
  arrays travel as typed binary buffers, planar per structure. **Complete for
  pre-1.0** (D0–D4 and the Qt payload scheme).
- [`runtime_message_router.md`](runtime_message_router.md) — envelopes, identity,
  authority and the shared action manifest. **Complete for pre-1.0** (R0–R4).
  `checkpoints.md` sends every new session to these two first.
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

- [`competitive_positioning.md`](competitive_positioning.md) — what the project
  competes on, what it concedes, and which concession is structural. Includes
  the agent-facing reading of the reproducibility thesis, and the two distinct
  design targets it implies — the agent operating the viewer, and the assisted
  human operating it.
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
- [`performance/startup_baseline_2026_07.md`](performance/startup_baseline_2026_07.md)
  — what a first canvas actually costs, split into one-time, per-viewer and
  per-load. Replaces the retired Numba JIT figures.

### Standalone

- [`standalone_direction.md`](standalone_direction.md) — **the decision, and the
  one to read first: one workbench model, multiple hosts.** Standalone is not a
  second product with its own interaction model or scene architecture.
- [`standalone_host_plan.md`](standalone_host_plan.md) — that direction turned
  into the operational pre-1.0 plan.
- [`standalone_supported_environment.md`](standalone_supported_environment.md) —
  the supported development-time environment recipe.
- [`standalone_packaging_strategy.md`](standalone_packaging_strategy.md) — how
  the host is packaged and distributed.
- [`standalone_qt_ci_and_gl_decisions.md`](standalone_qt_ci_and_gl_decisions.md)
  — CI and GL decisions closed on 2026-07-04 against a real GPU. **Not to be
  re-litigated without a new reason.** Spanish.
- *(`standalone_performance_and_depythonization.md` was archived on 2026-08-06:
  it argues from Numba JIT cold-start latency, and MolSysMT no longer uses
  Numba.)*
- [`standalone_v2_evolution_plan.md`](standalone_v2_evolution_plan.md) — post-1.0
  architecture for a v2 host, beyond the monolithic PySide6 prototype.

Closed Qt investigations live under [`audits/`](audits/README.md). The two
remaining product defects are tracked in
[`pending_bugs/standalone_qt_live_demo_reload.md`](pending_bugs/standalone_qt_live_demo_reload.md)
and [`pending_bugs/post_1.0/`](pending_bugs/post_1.0/README.md).

## Project direction

These documents explain product intent, not current implementation status.
Read them in this order: the first two say what the product *is*, the next three
scope 1.0, and the last four describe work that begins after it.

1. [`guiding_principles.md`](guiding_principles.md) — the ideas-alma: what the
   product is for, and what it refuses to become.
2. [`development_mantra.md`](development_mantra.md) — the practical conclusions
   that stay visible while writing code.
3. [`v1_vision_and_styles.md`](v1_vision_and_styles.md) — the 1.0 scope: half
   visualiser, half instrument, and what that costs.
4. [`scene_look_styles_direction.md`](scene_look_styles_direction.md) — the next
   careful step after the first scene-style slice.
5. [`style_battery_and_future_ideas.md`](style_battery_and_future_ideas.md) —
   which styles ship first, so style growth stays intentional.
6. [`molsysmovie_vision.md`](molsysmovie_vision.md) — post-1.0: a separate
   `MolSysMovie` surface for timelines and keyframes, kept out of the viewer.
7. [`render_quality_vision.md`](render_quality_vision.md) — post-1.0: **the
   project does intend to compete with desktop-quality rendering**, by bridging
   to Blender rather than replacing Mol\*.
8. [`future_vision_beyond_1_0.md`](future_vision_beyond_1_0.md) — post-1.0
   frontier ideas, including live streaming from a running simulation. Spanish.
9. [`areas_of_opportunity_analysis.md`](areas_of_opportunity_analysis.md) —
   five opportunity areas with feasibility analysis. Spanish. **Its "Estado
   Final de Implementación" sections record intent at the time of writing and
   have been contradicted by the code since; `scene_contracts.md` wins.**

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

### Say "done" where a scan will hit it

Documents are read by skimming, so **a closed item is only closed if that is
visible at scan depth**. Three rules follow, and this round is the evidence for
all three — a handoff rewritten in the morning still listed as open the three
things finished that afternoon, and an inventory of nineteen items had seven
bodies contradicting their own headers.

1. **The state goes in the title**, or in the first line of the file. Never only
   in the body: a reader who skims a long body concludes the work is pending, and
   the longer the body, the likelier that is.
2. **Text in place is inversely proportional to how closed something is.** A
   closed item keeps one line — the outcome and where the evidence lives. Its
   reasoning goes to `archive/`, or stays in the git history. Preserving a
   finished item's full *What / Why / How* beside the open ones is what makes an
   inventory read as a work queue.
3. **When you finish something, close it in its home document in the same
   change.** Not in a summary, not in a commit message: in the file the next
   reader will open.
