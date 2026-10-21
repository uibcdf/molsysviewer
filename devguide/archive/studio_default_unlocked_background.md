---
summary: Initialize Studio with background unlocked
issue: uibcdf/molsysviewer#252
status: resolved
opened: 2026-10-21
closed: 2026-10-21
verification: reproduced
area: [popup, ui, interaction]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Initialize Studio with background unlocked

**Reported:** 2026-10-21, TcTIM pre-1.0 dogfooding.

## What and how

Diego requests initial Studio/Add-ons with the lock open, permitting molecular rotation outside the card. Closed #237 defines local layout ownership but does not set this default.

FloatingPanelShell currently derives isAmbient from panelModeStyle == ambient, so the ordinary integrated/floating shell starts locked. Initialize shells unlocked, retain explicitly inherited false/locked state, and respect deliberate lock changes across closing/reopening. No new public Python configuration or global lock synchronization.

## Receiving plan

The bounded controls-visibility browser guard will assert the initial open-lock affordance and actual molecular rotation with Studio open, deliberate lock retention after reopening, and the external-canvas default. Scientific scene state and Dock remain unchanged.

## Resolution

The shared shell now initializes unlocked while explicit inherited/manual lock state remains authoritative. The real exported-view browser scenario rotates the molecular camera while Studio is open, then verifies a manual lock survives closing/reopening. The actual widget/canvas-popup scenario checks the inherited unlocked default.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`.
TypeScript, JS 330/330 and all three integrated browser scenarios pass; runtime
is rebuilt with `build:runtime`. [Receiving scopes](../studio_chrome_validation_20261021.json)
retain the open #251 caret investigation, human retest and hosted/installed
qualification separately. No new Python API, release or Qt qualification.
