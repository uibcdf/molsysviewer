# MolSysSuite Add-On Direction

This page records a future-facing but now operationally relevant direction for
**MolSysViewer 1.0**:

- **MolSysViewer should stay as a strong core workbench**
- **domain-specific MolSysSuite functionality should arrive through optional add-ons**

This direction is especially relevant for future integration with libraries
such as:

- `TopoMT`
- `PharmacophoreMT`
- `ElasNetMT`
- and other MolSysSuite packages with their own scientific semantics

## Core Position

`MolSysViewer` should not absorb all domain-specific analysis concepts into its
core runtime.

Instead, it should provide:

- a clean molecular workbench core
- a reproducible scene/state model
- and explicit extension points that allow optional ecosystem add-ons to grow on
  top of it

The goal is to avoid two bad outcomes:

- a bloated core viewer that tries to understand every downstream domain
- a fragmented ecosystem where each library builds a separate viewer shell

## What Must Stay Core

The following should remain part of the core `MolSysViewer` 1.0 workbench:

- canvas and popup runtime
- context menu
- `Navigate`
- `Workbench`
- generic shapes
- annotations
- measurements
- scene styles
- export / replay
- image-export foundation
- panel architecture
- the reproducible Python <-> TS scene/state contract

This is the common substrate that all MolSysSuite libraries should be able to
reuse.

## What Should Prefer Add-Ons

The following kinds of functionality should prefer optional add-ons rather than
growing the core directly:

- topography/cavity-specific analysis workflows
- pharmacophore-specific feature models and controls
- elastic-network or allostery-specific overlays and actions
- domain-specific figure/export helpers
- domain-specific panels and workbench summaries
- domain-specific context-menu actions
- domain-specific tool modes

This keeps the core thin while still allowing MolSysViewer to act as the shared
visual workbench of MolSysSuite.

## Main Visible Form Of An Add-On

The main visible form of an add-on should normally be:

- **one new panel**
- or, if scientifically necessary, a very small number of new panels

So, for example:

- `TopoMT` could register a `Topo` panel
- `PharmacophoreMT` could register a `Pharmacophore` panel
- `ElasNetMT` could register a `Network` or `Elastic` panel

This fits the panel-mode direction already established in `canvas_minimal_ux.md`
and avoids inflating the base workbench for users who do not need those
domains.

## What An Add-On May Register

The add-on surface should remain intentionally small and explicit.

Healthy registration targets include:

- one or more panels
- context-menu actions
- shape/overlay producers or adapters
- workbench summary sections or summary providers
- scene-style helpers or presets specific to that domain
- figure/export helpers for that domain
- optional tool modes

The panel is expected to be the main user-facing surface, but it should not be
the only possible extension point.

## What Should Not Be Opened Yet

The following should not be generalized prematurely, even if they remain future
evaluation targets:

- a large generic plugin marketplace model
- arbitrary runtime code loading from unknown packages
- deep host-specific UI forks
- unrestricted mutation hooks into the viewer core
- a huge add-on API before the base workbench is stable
- multiple competing extension mechanisms

For now, the healthy target is:

- **small, explicit extension points**
- **a plugin template or plugin tests**
- **no real domain plugin required yet**

## 1.0 Requirement

Even if `MolSysViewer 1.0` ships without real ecosystem plugins, it should
still:

- be architecturally compatible with add-ons
- expose clear extension points or entry hooks
- prove those hooks with at least one of:
  - a plugin test
  - a plugin template
  - a minimal fake add-on used only for validation

This is important because the point of 1.0 is not to ship all of MolSysSuite
inside MolSysViewer, but to ship a core viewer/workbench that the rest of
MolSysSuite can safely build on.

## Current Validation Slice

MolSysViewer now has a first explicit Python-side add-on registry surface split
into two levels:

- `molsysviewer.addons`
  - host-level registry
- `view.addons`
  - view-local projection of the host registry
- `AddonSpec`
- `AddonPanelSpec`
- `AddonContextActionSpec`
- `AddonWorkbenchSectionSpec`
- `AddonShapeProviderSpec`
- `AddonStyleHelperSpec`
- `AddonExportHelperSpec`
- `AddonToolModeSpec`
- `AddonLifecycleSpec`

This first slice is intentionally:

- explicit
- JSON-friendly
- host-aware
- registration-based rather than dynamic-code-loading-based

It is now validated through a combination of:

- fake add-ons in tests
- a small importable reference template:
  - `molsysviewer.addon_templates.minimal_topomt`
- public user/developer/cookbook docs that already describe the contract

This is the right first step because it fixes the shape of the connection
platform before real plugins start depending on it.

The important architectural decision is now explicit:

- add-ons are registered at the MolSysViewer host level
- views inherit that availability
- views may still enable/disable add-ons locally without redefining the host
  registry
- add-ons may now also expose a deliberately small per-view Python lifecycle:
  - `on_enable(view)`
  - `on_disable(view)`

## Near-Term Design Consequence

Current work toward 1.0 should therefore prefer:

- host-agnostic panel registration concepts
- panel-mode logic that can tolerate more than the two built-in panels
- summary/action registration that can be extended later
- generic shape management rather than hardcoding domain-specific assumptions
- minimal but real hooks, even before real plugins exist

## Suggested First Validation Strategy

Before any real ecosystem add-on is implemented, the project should likely
validate the extension shape using one of these:

- a minimal add-on template
- a fake test add-on
- a tiny internal proof-of-concept plugin used only in tests

This is preferable to waiting until a large real `TopoMT` or
`PharmacophoreMT` integration appears and discovering then that the core viewer
has no clean entry points.

## Discovery And Manual Coupling Direction

The first practical discovery model should stay simple and explicit.

Near-term preferred behavior:

- `MolSysViewer` keeps a small maintained list of known add-on module names
- `molsysviewer.addons.discover()` checks whether those modules are importable
- importable recognized add-ons are registered in the host registry
- missing modules are ignored without error

This is intentionally more conservative than a fully open dynamic plugin
discovery system.

It keeps the ecosystem easy to reason about while real MolSysSuite add-ons are
still few.

At the same time, there should also be an explicit manual path for local or
unpublished development:

- registering an `AddonSpec` directly
- or registering an importable add-on module explicitly

This manual path matters because early add-on authors should not need to
publish a conda package or wait to be added to a maintained discovery list
before validating their integration.

## Packaging Contract

The first packaging contract should remain lightweight and stable.

Recommended split:

- domain package:
  - `topomt`
- MolSysViewer integration package:
  - `molsysviewer-topomt`

Recommended importable module shape:

- package name:
  - `molsysviewer-topomt`
- importable module:
  - `molsysviewer_topomt`
- module should expose one of:
  - `addon`
  - `ADDON`
  - `get_addon()`

and that contract should resolve to an `AddonSpec`.

This keeps:

- the scientific package usable without MolSysViewer
- the viewer integration optional
- the import/discovery logic simple

For local development, manual coupling should support the same contract even
before publication:

- local module on `PYTHONPATH`
- explicit `molsysviewer.addons.register_module(...)`
- or direct `molsysviewer.addons.register(...)`

## Minimal Lifecycle Direction

The first runtime lifecycle now implemented should stay intentionally narrow:

- `AddonLifecycleSpec`
- `on_enable(view)`
- `on_disable(view)`

This should be understood as:

- Python-side
- view-local
- useful for light runtime setup/teardown

It should **not** yet be treated as:

- a broad hook framework
- a frontend execution contract
- a license to let add-ons mutate the whole host arbitrarily

This is the right intermediate step because it lets real add-on activation be
validated before a larger lifecycle model is opened.

## Relationship With Panel Minimalism

This add-on direction does not change the minimal UX rule:

- the resting canvas should remain clean
- add-ons should normally surface themselves through panel mode, not new
  permanent canvas chrome

In other words:

- extensions should mostly arrive as optional panel-mode growth
- not as new always-visible UI noise

## Open Questions

These questions remain intentionally open for later evaluation:

- should add-ons register full new panels, or also panel subsections?
- should add-ons contribute to `Workbench`, `Navigate`, or only as their own
  panels?
- how far should the initial maintained known-module list go before a more
  formal discovery mechanism is justified?
- should future discovery rely on entry points, package metadata, or keep a
  maintained-list path as the canonical safe fallback?
- how much of the extension model should be public API in 1.0 versus internal
  but tested?
- should the first proof-of-concept be a fake plugin or a real `TopoMT`
  integration?
- how should add-on enable/disable preferences be persisted across views or
  future standalone sessions?
- how much runtime lifecycle should be standardized in 1.0 beyond registration
  and discovery?
- when should the first add-on contribution become visibly real in the runtime,
  rather than only declared through specs and tests?

## Documentation Surfaces Required For 1.0

Even if `1.0` still ships without real ecosystem add-ons, the documentation
should already acknowledge the add-on model in all three major public-facing
surfaces:

- User Guide
  - what add-ons are
  - how they are installed
  - how discovery works
  - how they appear in the viewer
- Cookbook
  - a recipe for developing a minimal add-on
  - including the packaging contract and the expected exported object
- Showcase
  - at least one add-on-shaped scientific story
  - even if initially backed by a fake or internal proof-of-concept add-on

Developer documentation should also include:

- the host-level `molsysviewer.addons` model
- the local `view.addons` projection
- the packaging/discovery contract
- contribution types that an add-on may register
- testing strategy for add-on compatibility

This matters because the add-on platform should not only exist in code and
tests. It should also be teachable:

- to users installing optional scientific capabilities
- to developers extending MolSysViewer
- and to future MolSysSuite maintainers who need a stable extension model
