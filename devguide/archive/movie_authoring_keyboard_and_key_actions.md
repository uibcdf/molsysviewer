---
summary: Complete Movie workflow keyboard navigation and distinguish saved-key actions.
issue: uibcdf/molsysviewer#393
status: resolved
opened: 2026-11-14
closed: 2026-11-14
severity: medium
verification: reproduced
area: [movie, studio, accessibility, keyboard]
guard: molsysviewer/js/tests/e2e/movie-studio.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Movie authoring keyboard and key actions

M2's review finds a bounded gap in the new Movie workflow: the declared
tablist/tab roles have three keyboard tab stops, no horizontal arrow/Home/End
navigation and no associated labelled tabpanels. Native button activation and
the shared BasePanel focus/caret owner already exist and must be preserved.
The [W3C APG tabs pattern](https://www.w3.org/WAI/ARIA/apg/patterns/tabs/)
defines the expected semantics. This is not a claim that earlier Studio
keyboard work in closed #182 failed or that all controls are inaccessible.

Saved-key actions repeat `Remove key` without identifying track/time. The
three-decimal Edit labels can also collapse distinct fractional-second keys.
Use clear exact-time labels and stable per-key control identities, preserving
the Python recipe's existing milliseconds/seconds contract. Movie visual
time does not imply physical simulation time or change molecular data.

Extend the complete existing `movie-studio` real-Mol*/Python guard, retaining
its source/camera/preview/popups/export/encoder and cleanup assertions. Receive
tab/content traversal, automatic local arrow activation, wrap/Home/End and
native Space/Enter in the primary, canvas-popup and detached Studio paths.
Use two fractional times through the real UI/API and verify their retained
Python values and distinct editable actions. Navigation must preserve the
accepted plan and molecular state; form drafts retain their current owner.

This is a required focused M2 correction under #320/#315, not full accessibility
certification or completed native-Qt, installed or postponed human acceptance.
The running source CI `43654425383` retains its older exact input. Keep its
result separate from this later runtime/guard change; do not cancel it or
dispatch a duplicate while receiving this scope.

## Resolution — 2026-11-14

The panel retains one active tab stop and associated labelled content;
Left/Right wrap, Home/End and native Enter/Space preserve visible focus.
Explicit tab changes move focus after BasePanel restores the previous field.
Local navigation leaves Python's accepted recipe and physical scene unchanged.
Saved-key actions carry their track and full time, including raw milliseconds
in their accessible names, without fixed three-decimal visible rounding.

The complete guard fails before the correction with `[0, 0, 0]` rather than
`[0, -1, -1]` tab stops. That first assertion does not reproduce every later
assertion's failure. After the correction the same full entry passes, including
the primary, canvas popup and detached Studio keyboard paths, real Python
fractional-time key submission/editing, existing draft/camera/preview/PNG/AV1
checks and cleanup. All 491 JS cases and TypeScript also pass. The
[receipt](../movie_authoring_keyboard_receiving_20261114.json) records exact
inputs, limits and original outputs. This source closure does not complete
M2, #320 or hosted, actual-Jupyter/Qt, installed or human acceptance.
