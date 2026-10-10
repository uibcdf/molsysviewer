---
summary: Studio deletes scientific analyses without confirming scene-history loss
issue: uibcdf/molsysviewer#204
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: high
verification: reproduced
area: [studio, frontend]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio final review — analysis

**Reported:** 2026-10-10, final Studio review with real pentalanine and Mol*/Chromium.

## What
Delete analysis immediately deletes unreferenced scientific data and clears all scene Undo/Redo. The consequence appears only in a tooltip, with no confirmation.

## How
The Interactions panel emits delete_interaction_analysis directly. An isolated real Python view with an unreferenced hydrogen-bond analysis and an undoable sphere changes can_undo from true to false after delete_analysis.

## Why
Scientific data deletion must be distinguishable from undoable visual-set deletion. Add explicit confirmation naming the analysis and warning that it cannot be undone and clears scene history. Keep referenced analyses protected, correlate completion/errors, and guard cancellation and exact target selection.

## What was refuted

Deleting a visual set remains undoable and preserves named analyses. Clearing history on scientific deletion is the existing intentional Python contract; the missing part was explicit UI confirmation.

## Resolution

Stored-analysis deletion first opens a named inline confirmation explaining irreversibility and all scene Undo/Redo loss. Cancel emits no request; filtering cannot retarget the confirmation. Pending deletion is locked and its completion/error is correlated. The real browser guard checks cancellation, the warning and exact request target, actual removal and history clearing. tests/test_studio_creation_feedback.py verifies referenced analyses remain protected and successful deletion returns the correct acknowledgement.

**Executed:** 14/14 focused Python cases; TypeScript no-emit check; npm JS unit suite; real pentalanine/Mol*/Chromium Studio guard. These are source/development checks, not installed artifact qualification. The complete Python run and hosted gates retain their separate outcomes.
