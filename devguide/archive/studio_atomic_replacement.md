---
summary: Studio overwrites regions and selections without atomic rollback or reliable Undo
issue: uibcdf/molsysviewer#206
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [studio]
guard: tests/test_studio_replacement.py
normative:
blocked_by: []
supersedes: []
---

# Studio overwrites regions and selections without atomic rollback or reliable Undo

**Reported:** Final Studio review with the principal maintainer, 2026-10-10.

## What

Regions and Selections overwrite an existing tag by sending deletion and creation separately. Real pentalanine reproduction leaves the old region absent if recreation fails; isolated saved-selection replacement has no own Undo step; region Undo does not recover the old atom set in the tested route.

Observed on main a699f5b52729631643759942440c2afcb82e39f6 in the principal maintainer’s final Studio review.

## How

Use one validated owner operation/history boundary for replacement, preserve the old object on failure, and guard complete Undo/Redo. Include ordinary saved-selection creation in the history checks.

## Why

Authorized pre-1.0 Studio closure. Candidate 0.25.0 remains unfrozen; both 1.0 publications remain paused. Preserve real Python/Mol*/Chromium regression evidence.

## What was refuted

A successful normal-path smoke check does not cover rejection, replacement or exported backend availability. Source and live browser evidence do not qualify a frozen installed artifact.

## Resolution

One browser request carries the overwrite intent. Region creation/rename and saved-selection replacement/rename run existing owner operations inside `SceneHistory._atomic_operation`. Failed creation restores the complete prior scene and its Redo; successful replacement has one Undo/Redo step. Public saved-selection mutations now own scene history. Same-system state import retains their original descriptor, level and recipe.

`tests/test_studio_replacement.py` passes 8/8 on real pentalanine, asserting whole-scene equality for replacement, rollback and Undo/Redo, including ordinary public selection mutations. The real-Python/Mol*/Chromium `studio-list-workflows` guard also verifies single browser overwrite requests and both versions through Undo/Redo. The first Python guard exposed atom selections changing into group selections on restore; fixing the importer made the complete-scene assertion pass. No weakened assertion or skipped replacement.
