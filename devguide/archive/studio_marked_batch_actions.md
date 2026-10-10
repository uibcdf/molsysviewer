---
summary: Add explicit marked-item batch actions to native Studio saved lists
issue: uibcdf/molsysviewer#196
status: resolved
opened: 2026-10-09
closed: 2026-10-10
verification: reproduced
area: [studio]
guard: tests/test_studio_batch_actions.py
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Add explicit marked-item batch actions to native Studio saved lists

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Visibility and deletion require repeated individual actions for larger scenes.

## How

Mark rows independently from molecular selections; filter without expanding batch targets, prevalidate targets, apply supported actions with one undo record, confirm deletion inline and preserve interaction analyses.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

`SavedListTools` owns local marks, collapsed management controls, exact-target
inline deletion confirmation and correlated results. Marks remain independent
from atom selection and survive filtering. Actions apply to all marked items,
including filtered rows, as stated in the confirmation.

The Python batch route validates the complete list before mutation, calls
existing domain operations and uses `SceneHistory._atomic_operation` for one
Undo step and rollback on error. Only user layers can be ungrouped; their members
remain. Deleting an interaction visual set retains the scientific analysis.
The Python guard tests every domain, prevalidation/redo preservation, actual
operation failure/rollback and layer member preservation. The browser guard
checks exact filtered targets, confirmation/cancel, selection independence,
restored real annotation cells and preserved analyses. Focused Python 32/32 and
the final real browser guard pass.

## Final confirmation check — 2026-10-10

Changing marks with Mark matches also cancels a captured deletion confirmation,
as individual checkbox changes already do. The real saved-list browser guard
checks that this sends no molecular action and requires fresh confirmation.
