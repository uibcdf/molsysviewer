---
summary: Retire classic canvas controls from the pre-1.0 public surface
issue: uibcdf/molsysviewer#258
status: resolved
opened: 2026-10-21
closed: 2026-10-21
verification: reproduced
area: [controls, api, ui, configuration]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: docs/content/user/viewer/panel_mode.md
blocked_by: []
supersedes: []
---

# Retire the classic canvas controls

**Accepted direction:** Diego requests removing or deprecating the classic
controls during the 2026-10-21 manual smoke; they must not remain user choices.

## What

Offer the reviewed compact controls and Cinema. Remove Classic from context-menu
choices and supported new-call presets. Historical UI data needs a bounded
migration to the current controls, rather than resurrection of the old surface.
Panel layout options remain independently configurable.

## How

Update argument validation, configuration resolution, trait defaults, frontend
fallbacks, persistence readers, public guidance and affected fixtures together.
The manual notebook explicitly requests classic controls and must use the current
surface when retested; preserve its observed outputs before adapting its source.

## Why

The pre-1.0 public experience should expose the canvas controls already reviewed
with the context menu and Studio. This is independent of #257's invisible
shape-only geometry and does not authorize publishing a candidate.

## Outcome — 2026-10-21

Classic is removed from new public calls and the context menu. Diego also
approves canonical names `viewer_mode=standard|cinema` and
`controls_mode=compact|cinema`. Argument digestion, configuration, widget traits,
export/popup readers and remote/Qt defaults use those names. Historical UI
projections and stale configuration normalize to Standard/Compact; independent
panel layout identifiers, including integrated, remain unchanged.

The controls guard exercises the actual Python export and notebook bootstrap,
first-mount parity, legacy UI projections, Cinema cycles, context choices, both
canvas windows and scientific scene/playback convergence. The focused Python
guard `tests/test_view_mode_configuration.py` covers strict new-call rejection
with and without digestion, canonical defaults and configuration migration.

The [receiving record](../shape_only_controls_validation_20261021.json) preserves
local evidence and development diagnoses. Actual PHMT/Jupyter visual receiving
remains pending under #257; that separate defect is not closed by this proposal.
New hosted CI and candidate/artifact qualification retain their own scope.
