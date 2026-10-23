---
summary: Evaluate a dedicated Studio Loader entry before System
issue: uibcdf/molsysviewer#265
status: open
opened: 2026-10-22
closed:
verification: inspected
area: [studio, ui, loading]
guard:
normative:
blocked_by: []
supersedes: []
---

# Evaluate a dedicated Studio Loader entry before System

**Reported:** 2026-10-22, proposed by the principal maintainer during the
MolSysMT addon integration work.

## What

Evaluate moving the existing **Load systems** controls from **Studio > System**
into a dedicated **Studio > Loader** entry, placed first in the Studio menu,
before System. This records a design proposal; the interface is unchanged.

## How

`molsysviewer/js/src/ui/panels/system-panel.ts` currently mounts
`SystemLoadControls` alongside the system header, context inspector and molecular
strips. `system-load-controls.ts` owns the loading controls. Review that seam to
separate the loading workspace while retaining System for inspecting and
presenting the loaded molecular system.

Before implementation, decide:

- Whether a separate entry improves discovery enough to justify another panel
  switch, and whether Loader is the clearest name.
- Which panel opens by default for empty and populated views; appearing first
  in the menu need not mean reopening Loader after every load.
- What Loader and System show before, during and after loading, including
  failures and repeated additions.
- How existing welcome and contextual loading entry points reach the same
  controls, without duplicate loading implementations.
- How the layout behaves in small notebook outputs, fullscreen, the canvas
  popup and the detached Studio popup.

Reuse the current loading tools and Python API. The proposal changes navigation,
not molecular loading semantics or ownership. Single-source, batch and
progressive loading, source selection and diagnostics must remain available.

## Why

Loading is the entry into the visualization workflow. A dedicated first entry
could make that action easier to find and reduce the responsibilities and
visual density of System. The cost is additional navigation and separation
between loading and inspecting the resulting system; the design review must
compare both arrangements against a relaxed, simple workflow.

## What was refuted

No design alternative has been rejected yet. The all-state issue search found
no equivalent proposal. uibcdf/molsysviewer#151 concerns the existing molecular
loading contract, rather than this navigation decision. The ongoing addon
receiving work in uibcdf/molsysviewer#264 is independent of it.

## Acceptance

Record the selected arrangement, responsibilities and empty/loaded behavior
before implementation. If adopted, add browser guards covering the loading
entry points, preserved workflows and popup parity. No release milestone or
immediate interface change is assigned by this report.
