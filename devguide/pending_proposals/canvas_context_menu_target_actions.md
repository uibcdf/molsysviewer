---
summary: Redesign the canvas context menu for contextual core workflows before 1.0
issue: uibcdf/molsysviewer#179
status: partial
opened: 2026-10-08
closed:
verification: inspected
area: [canvas, interaction, selection, studio]
guard:
normative:
blocked_by: []
supersedes: []
---

# Contextual core workflows in the canvas menu

**Reported:** 2026-10-08, during the principal maintainer's pre-1.0 design
review. The maintainer approves the proposed redesign as a pre-1.0 requirement.
The menu foundation is implemented and has new real-browser coverage. Molecular
target workflows, object/occurrence workflows and human review remain pending.

## What

Provide a compact canvas menu with actions on the clicked target, a separately
identified active selection, and shared view/history/Studio access. Give users
explicit selection, inspection and contextual creation operations. Interaction
actions distinguish the picked occurrence, its graphical set and the stored
analysis. Configuration opens the appropriate existing Studio section.

The accepted layouts, staged implementation and acceptance scenarios are in
[`../canvas_context_menu_pre_1_0_plan.md`](../canvas_context_menu_pre_1_0_plan.md).
This report tracks one product surface; the execution plan stays outside the queue.

## How

The inspected baseline in `molsysviewer/js/src/ui/context-menu.ts` rendered repeated measurement
variants, active-selection expanders, every saved selection and rows of relevant
regions in a scrolling flat menu. The foundation replaces this with bounded
submenus and Studio collection navigation, uses the available residue identifier
and exposes shared view controls on all target families. Explicit molecular
selection and direct target creation are still pending.

`molsysviewer/js/src/managers/viewer-controller.ts` resolves picked interactions
to participant atoms and an entity reference with analysis name/revision, frame
and occurrence index. The menu uses the set tag for focus/delete, leaving this
occurrence context unused. Panel labels may advertise closing while controller
branches opened the corresponding panel. The foundation now uses an explicit
Open Studio action and establishes menu-first Escape. The unused occurrence
context remains a pending seam.

Reuse the existing scene-object, selection, history and Studio owners. Introduce
shared applicability and target resolution rather than a second set of scene
mutations. The existing observation actions require matching query revisions and
an inspected page; connecting a pick needs a bounded resolution path, not merely
forwarding its entity reference. Reject stale frame/analysis/filter contexts.

## Why

The maintainer accepts the public API and Studio organization as adequate for
1.0, but finds the menu an incomplete entrance to the same core workflows.
The redesigned surface should make ordinary scientific interaction discoverable
without silently replacing a working selection or starting expensive calculations.

Preserve right-drag pan, named analysis persistence, experimental scientific
status, sparse queries, explicit quantities, and region hide/disable ownership.
The new menu requires a new candidate; the existing 0.24.1 files and their
qualification retain their original identities and scope.

## What was refuted

- Full collection management inside the menu makes its size depend on the scene;
  retain collection editors in Studio and only bounded relevant context entries.
- Deleting a picked interaction is not equivalent to removing its graphical set
  or stored analysis. Do not offer unsupported occurrence editing.
- A generic atom-hide mask would change the agreed region/Whole ownership model.
  Contextual creation and existing region operations preserve that model.
- One-shot explicit atom/residue/chain selection does not require adopting the
  deferred global picking-preference proposal (`uibcdf/molsysviewer#45`).
- Existing source and package certificates cannot qualify changed menu code.
  Preserve the prior campaign and qualify the replacement candidate separately.

## Implementation evidence — 2026-10-08

`MenuNavigation` owns compact in-card pages, keyboard navigation, Back and focus;
`ViewerContextMenu` owns applicability, headings and bounded collection access.
Studio section navigation reuses `GroupPanel.openSection`. Browser-owned layout
actions are consumed locally, and the menu emits a single event for mutations.
Viewport requests carry their desired state through the real Python handler,
avoiding a second toggle on its echo. History availability follows the backend.

The real dialanine/Mol*/Chromium guard
`molsysviewer/js/tests/e2e/context-menu.e2e.ts` passes, including menu/selection
separation, keyboard/focus, viewport echoes, Studio routing, scene history,
atomless applicability, bounds and Escape priority. The 17 focused menu unit
cases and TypeScript check pass. The full JS campaign passed 323/323 before the
last dispatch refinements; focused owner/browser checks cover those refinements.
The core browser campaign exposed one old test that clicked a now-collapsed
selection action; its navigation is corrected and its targeted rerun passes.
The original failure is retained separately from the remaining-suite recovery.
All 40 distinct core browser suites now have passing evidence: 16 from the
initial campaign, the corrected GroupPanel suite from its targeted rerun, and
23/23 from the unexecuted-suite recovery. This is not one uninterrupted green
campaign. The extended menu guard separately verifies the final dispatch fixes.
Runtime regeneration, 181 reporting-protocol checks and generated-index checks
pass; the board state label is synchronized to partial.
This is development evidence, not installed-package or human acceptance.

## Resolution

Pending remaining implementation and the principal maintainer's remote-Jupyter
acceptance. Current interaction guidance records the delivered foundation;
archive this report and close #179 only with addressable guards and evidence.
