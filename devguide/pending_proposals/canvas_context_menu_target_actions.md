---
summary: Redesign the canvas context menu for contextual core workflows before 1.0
issue: uibcdf/molsysviewer#179
status: open
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
Implementation and new browser verification have not started.

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

`molsysviewer/js/src/ui/context-menu.ts` currently renders repeated measurement
variants, active-selection expanders, every saved selection and rows of relevant
regions in a scrolling flat menu. Molecular headings omit the residue identifier
already available in target metadata. Molecular targets lack explicit selection
and direct region/annotation creation. General view controls appear on empty
canvas rather than consistently across target families.

`molsysviewer/js/src/managers/viewer-controller.ts` resolves picked interactions
to participant atoms and an entity reference with analysis name/revision, frame
and occurrence index. The menu uses the set tag for focus/delete, leaving this
occurrence context unused. Panel labels may advertise closing while controller
branches open the corresponding panel. Global Escape handling does not establish
menu-first dismissal. These are source-inspection findings, not newly reproduced
browser failures.

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

## Resolution

Pending implementation, real-browser guards and the principal maintainer's
remote-Jupyter acceptance. Update current interaction guidance at delivery;
archive this report and close #179 only with addressable guards and evidence.
