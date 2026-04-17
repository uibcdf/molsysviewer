# ElasNetMT Add-On Plan

Last update: 2026-04-17

This note records the current development plan for an **ElasNetMT add-on** on
top of the now-explicit MolSysViewer add-on platform.

It is meant to be operational, not aspirational.
The goal is to define a realistic path that matches the current host/runtime
contract instead of designing against a future plugin system that does not yet
exist.

## Why ElasNetMT Should Arrive As An Add-On

`ElasNetMT` is exactly the kind of domain-specific functionality that should
*not* be absorbed into the MolSysViewer core.

The core viewer should continue to own:

- shared molecular rendering
- shared workbench/runtime
- generic overlays and selections
- replay/export/state behavior

The `ElasNetMT` integration should own:

- elastic-network model semantics
- network-specific overlays
- mode-specific visual helpers
- allostery/anisotropy-specific actions
- domain-specific figure/export helpers

This keeps the host coherent while still letting MolSysViewer act as the shared
visual workbench of MolSysSuite.

## Product Position

The ElasNetMT add-on should be treated as a **large add-on**.

That means the preferred visible form is:

- one workspace
- a small local panel stack
- one or more workbench sections
- a few context actions
- one or more shape/overlay producers
- one export helper

Recommended first user-facing workspace:

- workspace id:
  - `elasnetmt`
- workspace title:
  - `Elastic Networks`

## Important Constraint: Current Host Capability

The current add-on platform is already credible, but it is still intentionally
conservative.

The parts that are real today:

- host-level registration through `molsysviewer.addons`
- per-view activation through `view.addons`
- visible runtime summary in the shared `Workbench`
- visible workspace + panel-stack projection
- context-menu actions routed back to Python
- minimal per-view lifecycle:
  - `on_enable(view)`
  - `on_disable(view)`
  - `on_context_action(view, action_id, payload)`

The parts that are *not* the right target for the first ElasNetMT slice:

- rich arbitrary frontend panel execution
- broad plugin marketplaces
- unrestricted runtime hook systems
- host-specific UI forks

So the first ElasNetMT slice should be **Python-driven and overlay-first**.

## Visual Primitives Already Available

MolSysViewer already has the primitives needed for a strong first ElasNetMT
prototype:

- contact graphs:
  - `view.shapes.add_links(...)`
- mode displacement arrows:
  - `view.shapes.add_displacement_vectors(...)`
- anisotropy glyphs:
  - `view.shapes.add_anisotropy_ellipsoids(...)`

This matters because it means the first add-on does not need new rendering
infrastructure in MolSysViewer core to become useful.

## Recommended Package Direction

Long-term package split:

- scientific/domain package:
  - `elasnetmt`
- MolSysViewer integration package:
  - `molsysviewer-elasnetmt`
- recommended Python import name:
  - `molsysviewer_elasnetmt`

Short-term validation path inside the MolSysViewer repo:

- keep one bundled **reference ElasNetMT add-on** in `molsysviewer.addon_templates`
- use it to validate:
  - workspace shape
  - runtime summary
  - lifecycle
  - context action routing
- only then move or duplicate the implementation into the external integration
  package

This is the right sequencing because it keeps host pressure visible while
avoiding premature packaging churn.

## MVP Scope

The first meaningful MVP should do only a few things, but do them well:

1. expose one `Elastic Networks` workspace
2. expose a small panel family:
   - `Model`
   - `Modes`
   - `Figures`
3. expose one or two workbench sections:
   - `Modes`
   - `Network Overlays`
4. expose at least two context actions:
   - `Show Contact Network`
   - `Show Mode Vectors`
5. expose one export helper:
   - `ENM Figure Export`
6. keep runtime behavior in Python lifecycle hooks

The MVP should *not* try to be a complete ENM application inside the viewer.

## Execution Phases

### Phase 1. Host Validation Slice

Goal:

- prove that an ElasNetMT-shaped domain can live credibly inside the current
  add-on host

Work:

- add a bundled reference add-on template shaped like ElasNetMT
- register it through `addon_templates`
- add tests for:
  - registration
  - lifecycle
  - context action routing
  - runtime summary

Deliverable:

- a stable reference module such as:
  - `molsysviewer.addon_templates.minimal_elasnetmt`

### Phase 2. Runtime State Model

Goal:

- define the minimal per-view state that a real ElasNetMT add-on needs

Work:

- establish runtime keys stored on the `view`
- define conservative cached state for:
  - active model kind (`GNM` or `ANM`)
  - node selection
  - cutoff
  - active mode index
  - visible overlay tags

Deliverable:

- a Python-side runtime contract simple enough to stay testable and replay-safe

### Phase 3. Overlay Adapters

Goal:

- translate ElasNetMT outputs into existing MolSysViewer shape APIs

Work:

- adapter for contact maps -> `add_links(...)`
- adapter for normal modes -> `add_displacement_vectors(...)`
- adapter for anisotropy -> `add_anisotropy_ellipsoids(...)`

Deliverable:

- pure adapter functions with stable tags, ready for lifecycle/context-action
  use

### Phase 4. First Real Actions

Goal:

- make at least one real scientific action visible and reproducible

Work:

- implement `Show Contact Network`
- implement `Show Mode Vectors`
- keep both routed through `on_context_action(...)`

Deliverable:

- one add-on that is no longer only metadata and runtime summaries

### Phase 5. Figure/Export Layer

Goal:

- make ElasNetMT output reusable in publication-oriented work

Work:

- define one export helper for standard ENM figures
- support figure recipes such as:
  - structure + network
  - structure + one mode
  - structure + anisotropy glyphs

Deliverable:

- a domain-specific export story that still sits on the shared host

## Technical Principles

The ElasNetMT add-on should follow these rules:

- prefer **Python-side orchestration**
- prefer **existing MolSysViewer overlays**
- prefer **stable tags** over ad hoc runtime mutation
- prefer **replayable actions** over ephemeral UI-only interactions
- avoid forcing MolSysViewer core to understand ENM semantics too early

## Non-Goals For The First Slice

Do not treat the first slice as the place to solve:

- the final frontend panel execution model
- a broad plugin marketplace
- persistent add-on user preferences
- arbitrary per-frame ENM animation controls in the frontend
- large host-side abstractions for all possible downstream science domains

The right first proof is narrower:

- one real domain
- one real runtime
- one real overlay path
- one real export helper

### Phase 6. Interactive Panel Widgets (done 2026-04-17)

Goal:

- give each ElasNetMT panel a real interactive UI embedded in the canvas panel
  host, without requiring TypeScript or MolSysViewer-internal knowledge

Work:

- `AddonPanelWidget` base class added to `molsysviewer.addons` ✓
- `widget_class` field added to `AddonPanelSpec` ✓
- `ViewAddonsManager.resolve_panel_widget(addon, panel)` ✓
- TS panel host in `workbench-panel.ts` + ESM model proxy in
  `viewer-controller.ts` ✓
- Python panel lifecycle in `viewer/core.py`:
  - `panel_navigate` → `_mount_addon_panel` ✓
  - `panel_unmount` → `_unmount_addon_panel` ✓
  - `addon_panel_action` → routes to active widget ✓
- `ElasNetMTModelPanel` in `molsysviewer_elasnetmt/panels/model.py`:
  - GNM/ANM tab toggle, cutoff input, Compute button ✓
  - `on_mount` pushes initial runtime state ✓
  - `handle_action` handles `set_model_kind`, `set_cutoff`, `compute` ✓
  - `compute` action builds and caches the GNM/ANM model via existing adapters ✓
- 4 new integration tests in `test_molsysviewer_addon.py` ✓

Deliverable:

- the first real interactive add-on panel is embedded and working end-to-end

## Current State

Phases 1–6 are complete. All three ElasNetMT panels have interactive widgets:

- `ElasNetMTModelPanel` (`model`): GNM/ANM toggle, cutoff, Compute ✓
- `ElasNetMTModesPanel` (`modes`): mode index selector, Show Vectors ✓
- `ElasNetMTFiguresPanel` (`figures`): preset selector, format toggle, Export ✓

19 integration tests in `tests/integration/test_molsysviewer_addon.py` — all passing.

The ElasNetMT add-on is now a complete proof of the `AddonPanelWidget` contract.
No structural work pending in either `molsysviewer` or `molsysviewer_elasnetmt`.
