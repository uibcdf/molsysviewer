# Developer Guide

Welcome to the technical documentation for **MolSysViewer**. This guide is intended for developers who wish to contribute to the library or understand its inner workings.

## Source of Truth

For development work in this repository, `devguide/` is the source of truth.
The purpose of `devguide/checkpoints.md` is not to duplicate git history.
Git already records the historical sequence of changes.

`devguide/checkpoints.md` should instead be maintained as the current working
checkpoint for the next developer session. It should make clear:

- where we are now,
- what is already decided,
- what we think should happen next,
- why that is the right next step,
- and what criteria/invariants must be preserved.

## Guiding Principles

MolSysViewer is not being developed merely as an interactive molecular viewer.

Its guiding principles are recorded separately in:

- [Guiding Principles](guiding_principles.md)

The first one already adopted is:

- scientific work has an interactive and exploratory phase,
- but scientific results must remain reproducible.

That principle should guide prioritization throughout the repository.

## Contents

1. [**Architecture**](architecture.md)
   - The Python/JS bridge, Mol* integration, and messaging protocol.
1. [**Scene Contracts**](scene_contracts.md) — **normative**
   - How regions relate to the whole, to colour, to ordering and to persisted state.
     Representation states (None/Inherit/Own), the colour layer stack, regions as recipes,
     state v2, the scene history. **Read before changing any of it.**
1. [**Engineering Rules**](engineering_rules.md)
   - How we are allowed to build: API first, generated artefacts, what a test must assert,
     the mutation audit, and what "green" means.
2. [**Digestion and Dependencies**](digestion_and_dependencies.md)
   - Using ArgDigest for validation and DepDigest for environment robustness.
3. [**Units and Quantities**](units_and_quantities.md)
   - Policy for physical magnitudes: quantities required, bare numbers rejected.
4. [**SMonitor Integration**](smonitor.md)
   - Diagnostics, catalog rules, and telemetry signals.
4. [**Interaction Overview**](interaction_overview.md)
   - Entry point for interaction design, decisions already closed, and implementation order.
5. [**Interaction Targets and Selection**](interaction_targets_and_selection.md)
   - Target taxonomy, picking levels, `active_selection`, mixed selection, and group metadata.
6. [**Interaction Gestures and Menus**](interaction_gestures_and_menus.md)
   - Hover/click/double-click semantics, context menus, and measurement/tool-mode behavior.
7. [**Interaction Modifiers and Future**](interaction_modifiers_and_future.md)
   - Reserved modifiers, future ideas, borrowed patterns, and deferred questions.
8. [**Interaction Verified State**](interaction_verified_state.md)
   - Operational truth of what gestures and interaction surfaces are already implemented and smoke-verified.
9. [**Strips**](strips.md)
   - GroupStrip direction, alternatives not chosen, first implementation scope, and future strip ideas.
10. [**Annotations**](annotations.md)
   - Viewer taxonomy for labels/annotations, Mol* precedents, and the first annotation slice.
11. [**Selections**](selections.md)
   - Persistent named selections as a category distinct from regions.
12. [**Smoke Test**](smoke_test.md)
   - Short runbook for checking interaction feel and reproducibility together.
13. [**Guiding Principles**](guiding_principles.md)
   - Stable project ideas-alma that should guide development and usage.
14. [**Development Mantra**](development_mantra.md)
   - Short identity guide: differentiation, health assessment, risks, and the decision filter to avoid drift.
15. [**Roadmap**](roadmap.md)
   - Strategic goals and upcoming development phases.
16. [**Checkpoints**](checkpoints.md)
   - Current handoff checkpoint: active status, decisions, next steps, and constraints.
17. [**Vision for v1.0**](v1_vision_and_styles.md)
   - Architectural vision, user personas, and the concept of scientific Styles.
18. [**Styles: First Slice**](styles_first_slice.md)
   - Narrow technical contract for introducing the first public `Style` object on top of the existing representation/preset base.
19. [**Styles: Second Slice And Project Config**](styles_second_slice_and_project_config.md)
   - Priority order for style interaction channels and the proposed `_molsysviewer.py` path for embedders.
20. [**Style Battery And Future Ideas**](style_battery_and_future_ideas.md)
   - Canonical first battery of scene recipes and tracked future directions inspired by Mol* and nglview.
21. [**Scene Look Styles Direction**](scene_look_styles_direction.md)
   - Clarifies the future distinction between scene recipes and visual looks such as `default-look` and `illustrative`.
22. [**Canvas Minimal UX**](canvas_minimal_ux.md)
   - Minimalist canvas/popup UX direction: only two interaction doors, three permanent meta-controls, and panel mode as the structured workspace entrypoint.
23. [**Standalone Direction**](standalone_direction.md)
   - Medium-term direction for a CLI/standalone host built on the same workbench and reproducible runtime, not a separate product.
24. [**Standalone Host Plan**](standalone_host_plan.md)
   - Concrete pre-`1.0.0` plan for the final standalone host, host options considered, and the preferred app-shell direction.
25. [**Standalone Qt Prototype Plan**](standalone_qt_prototype_plan.md)
   - Technical mini-plan for the first `PySide6 + Qt WebEngine` prototype and the thin-host boundary it must preserve.
26. [**Standalone Supported Environment**](standalone_supported_environment.md)
   - Supported development-time recipe for the Qt host spike and the current conda/pip boundary.
27. [**Standalone Packaging Strategy**](standalone_packaging_strategy.md)
   - Current position on supported recipes, packaging options still open, and when final standalone distribution should be decided.
28. [**Image Export Direction**](image_export_direction.md)
   - Work lines, roadmap, premium/publication goals, and open questions for image export on top of the current Mol* runtime.
29. [**MolSysSuite Add-On Direction**](molsyssuite_addon_direction.md)
   - Core-vs-add-on boundary for MolSysViewer, optional ecosystem panels, and the requirement that 1.0 already leave plugin entry points or a template/test in place.
30. [**Path to 1.0.0 (Unified Release Plan)**](path_to_1_0.md)
   - Unified roadmap for the stable 1.0.0 release, integrating competitive quality gaps and strategic milestones.
31. [**ElastNetMT Add-On Plan**](elastnetmt_addon_plan.md)
   - Concrete integration plan for the ElastNetMT add-on, using the existing overlay primitive set (links, displacement vectors, anisotropy ellipsoids).
32. [**Course Structure**](course_structure.md)
   - Proposed 23-module curriculum for an "Introduction to MolSysViewer" course, from basic loading to advanced cinematic production.
33. [**MolSysMovie Vision**](molsysmovie_vision.md)
   - Original strategic vision for cinematic/VR animation. VR direction remains post-1.0.
34. [**MolSysMovie Plan**](molsysmovie_plan.md)
   - Concrete pre-1.0 architecture and phased plan for `view.movie`: JS animation engine,
     keyframe timeline, serializable recipes, and export pipeline.
35. [**Load Modes and Append Structures Status**](load_modes_and_append_structures_status.md)
   - Reference status document for `load()` mode variants and the structure-append workflow.
36. [**Performance Benchmarks**](benchmarks/README.md)
   - Benchmark suite specifications, execution instructions, and runtime optimization roadmaps.
37. [**Render Quality Vision**](render_quality_vision.md)
   - Strategic vision for high-fidelity rendering and Blender integration (post-1.0).
38. [**Mol\* Color Strings**](molstar_color_strings.md)
   - Baseline record of named color strings that MolSysViewer treats as valid Mol\* color names.
39. [**Standalone Performance and De-pythonization Roadmap**](standalone_performance_and_depythonization.md)
   - Long-term strategy for addressing JIT/Numba latency and transitioning to Rust/WASM.
40. [**Standalone Version 2 Evolution Plan**](standalone_v2_evolution_plan.md)
   - Architectural roadmap for transitioning to a zero-configuration, lightweight desktop app for non-programmers.
41. [**pytest-receptor**](pytest_receptor.md)
   - Compact, agent-oriented output for the Python test suite; that it is pre-1.0, and where to report anomalies and proposals.
42. [**Studio Interactions Subpanel UI Specification**](pending_proposals/studio_interactions_subpanel_ui_design.md)
   - UX/UI design specification for the upcoming Interactions subpanel (InteractionsPanel), covering Mode A/B/C creation forms, contact persistence sparklines, and unified Studio card semantics.



## Workbench Tutorials (Planned)

To bridge the gap between API reference and real-world scientific usage, the following case-study-driven tutorials are prioritized for the v1.0 release:

- **Pocket Contact Analysis**: Identifying a binding pocket, using the `GroupStrip` for hierarchical selection, labeling residues, and measuring key distances.
- **Complex System Navigation**: Managing systems with multiple chains, ligands, and solvent molecules using the new hierarchical `GroupPanel` and selection tools.
- **Structural Mutation Replay**: Demonstrating how annotations and measurements survive structural rebuilds when modifying systems from Python.

## The scene reworks: **done** (2026-07-11 and 2026-07-14)

A 2026-07-10 audit found that the Regions and Whole subpanels rested on unwritten contracts that
the code silently violated, plus a ~3-second-per-message performance toll. A 15-phase rework fixed
it. The plan, the per-subpanel blueprints and the phase briefs are gone — they were scaffolding,
and git has them. What survives is what future work must obey:

- [`scene_contracts.md`](scene_contracts.md) — **normative.** Representation states
  (None/Inherit/Own), layered colour and ordering, regions-as-recipes, state v2, the scene
  history, and the identity, ownership, persistence, and visibility rules for shapes,
  annotations, measurements, and layers. Wins over every other document.
- [`engineering_rules.md`](engineering_rules.md) — the rules the rework was built under, and the
  defects that earned each of them.

Regions, Whole and Layers now have real subpanels; the Studio no longer reaches past the Python
API to repaint Mol\*; and the contracts are guarded on screen by
`js/tests/e2e/scene-contracts.e2e.ts`.

`docs/` and `bloques.md` were migrated. **`sandbox/Curso/` was deliberately not** — it is the
maintainer's working area and still calls the pre-rework API. See `scene_contracts.md` §Migration.

## Standing requirement: session reproducibility

- [`session_reproducibility.md`](session_reproducibility.md) — the durable rule that a user
  must be able to save a session and reload it later, unchanged. Any state a user can create
  must round-trip through `export_state` / `import_state`, or the promise breaks **silently**.
  Read it before adding any new kind of scene state.

## Standards and Conventions

This project strictly adheres to the UIBCDF software engineering standards. Please refer to the root `*_GUIDE.md` files for the canonical documentation of each infrastructure tool.

For MolSysViewer add-ons, there is now also a local standards layer that should
be maintained together with the runtime contract and public docs:

- [`standards/addons/README.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/README.md)
- [`standards/addons/IMPLEMENTATION_CONTRACT.md`](/home/diego/repos@uibcdf/molsysviewer/standards/addons/IMPLEMENTATION_CONTRACT.md)
