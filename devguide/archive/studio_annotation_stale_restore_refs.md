---
summary: Annotation cleanup after scene restore removes stale Mol* transforms
issue: uibcdf/molsysviewer#199
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: high
verification: reproduced
area: [studio, annotations, history]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Annotation cleanup after scene restore removes stale Mol* transforms

## What

The real saved-list browser guard fails during Undo of marked shape visibility
in a pentalanine scene with atom-anchored annotations. Annotation cleanup calls
Mol* RemoveObject on a transform already removed with the preceding structure.
The browser throws `TypeError: Cannot read properties of undefined (reading 'parent')`.

## How

`studio-list-workflows.e2e.ts` uses the real Python history snapshot/restore and
Mol* state. `AnnotationHandlers.clearLabels` retains stale references and
removes them concurrently with `removeParentGhosts: true`. Installed Mol* 5.4.1
`mol-plugin/behavior/static/state` and the local upstream source agree that this
command expects an existing transform before dereferencing its parent.

## What was refuted

Python history tests alone do not exercise stale Mol* state references. Increasing
timeouts or swallowing existing-reference removal errors would hide the defect.

## Resolution — 2026-10-10

Both complete and tag-specific annotation cleanup call one reusable owner-local
operation. It checks the current transform before each sequential removal.
References already removed by a structure rebuild are skipped; errors removing
existing refs still propagate. The implementation does not catch arbitrary Mol*
exceptions. Installed Mol* and the local upstream RemoveObject implementation
both require an existing transform when removing ghost parents.
The final real browser guard performs Undo against real Python/Mol* and asserts
restored annotation representation cells, not merely saved sidebar rows. It passes;
JS unit regression also passes with state-aware cleanup fixtures.
