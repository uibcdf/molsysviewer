---
summary: Secondary saved-selection forms lose their draft and focus on panel reconstruction
issue: uibcdf/molsysviewer#193
status: resolved
opened: 2026-10-09
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Secondary saved-selection forms lose their draft and focus on panel reconstruction

**Reported:** 2026-10-09, second Studio review and authorized refinement.

## What

Inline saved-selection editors are recreated without persistent editor state or a field identity. BasePanel therefore cannot restore the current form and draft across canonical updates.

## How

Give editors stable identity and local draft state, preserve focus/caret across updates and tab changes, and reconcile renamed/deleted targets without acting on replacements.

## Why

The principal maintainer authorizes this refinement round before the next 0.25.0 candidate freeze. Both 1.0 publications remain paused. Consumer source: 01208af0 after the first Studio round. Implementation must retain real molecular/browser guards, native backend ownership and explicit qualification scope.

## What was refuted

Source signature inspection is not full scientific/artifact qualification. No publication is authorized by this implementation.

## Resolution — 2026-10-10

Saved-selection editors own their open mode and value outside DOM nodes.
`EditorDrafts` retains secondary text keyed by control/object while canonical
values are unchanged. BasePanel preserves focus/caret and avoids triggering
annotation blur completion during repaint. Measurement/layer creation names are
model state. Missing targets prune marks, drafts and open editors even when their
panel is hidden; deletion followed by Undo cannot resurrect an old draft.
The final real browser guard checks focused selection edits, unfocused annotation
renames, cancellation, frame/tab changes, hidden deletion/Undo and pending
measurement/layer names. It passes with real Python and Mol*.
