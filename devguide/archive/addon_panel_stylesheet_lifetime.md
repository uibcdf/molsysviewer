---
summary: Addon render content replacement removes its host-provided CSS.
issue: uibcdf/molsysviewer#298
status: resolved
opened: 2026-11-05
closed: 2026-11-05
severity: medium
verification: reproduced
area: [addons, ui]
guard: molsysviewer/js/tests/unit/addon-panel-lifecycle.test.ts
normative: devguide/addon_panel_widget_contract.md
blocked_by: []
supersedes: []
---

# Addon stylesheet lifetime

## What

An addon that replaces its ESM render element's content loses the stylesheet
declared in `_css`. The resulting controls work but use browser-default styling.

## How

The real MolSysMT System panel on the 7d9f689c host exposed unstyled controls
while rendering real 1TCD. The host placed the style element inside the same
element passed to `render`, where normal `innerHTML` replacement removed it.
Computed layout therefore disagreed with the declared flex stylesheet.

## Why

The host promises independent `_css` and replaceable content. A consumer-side
duplicate stylesheet would conceal the generic host defect and complicate
cleanup in independent windows.

## Resolution

A host-owned wrapper contains the style and a separate replaceable render
element. The new unit regression replaces content at initial mount and again
after rendering, asserting that the wrapper still owns the stylesheet.
Existing cleanup checks remain in the same registered Node lane. The real
Mol*/ESM/Python browser exercise checks computed flex layout, absence of panel
styles after unmount and reapplied styles after remount, together with native
selection/removal and synchronization recovery. CSS remains scoped document
CSS, not shadow-root isolation. No scientific or consumer-specific host code
is introduced.

The local bounded unit profile is documented in the reporting protocol and
validated offline. Headless browser evidence does not certify live Jupyter,
visible Qt, real popups or installed packages. Hosted CI remains separate.
