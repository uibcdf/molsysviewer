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
- how should add-on discovery/installation work in Python environments?
- how much of the extension model should be public API in 1.0 versus internal
  but tested?
- should the first proof-of-concept be a fake plugin or a real `TopoMT`
  integration?
