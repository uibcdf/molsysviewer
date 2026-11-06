---
summary: Rejected direct state imports erase existing scene objects before validation finishes.
issue: uibcdf/molsysviewer#317
status: active
opened: 2026-11-06
closed:
severity: high
verification: reproduced
area: [state, history, lifecycle]
guard:
normative:
blocked_by: []
supersedes: []
---

# Direct state rejection erases open work

**A2 — active; P1; covering artifact and accepted 1.0 scope.** Viewer owns #317
under #315. A real-system rejection guard is the next observable gate, followed
by restoration/history/session receiving. No scientific provider fix is needed.

## Observation and duplicate review

An invalid later clipping section is rejected after `_clear_state_for_import`
has removed an existing region. Molecular coordinates remain unchanged, but
the exported scene differs after the exception. A fresh benign receiver on
the execution source reproduced the loss independently of the original audit.

All four issue pages were acquired before filing. Closed #127 protects session
loading with an isolated candidate, while direct `import_state` and `load_state`
still publish parts of restoration before complete validation. Closed #120 and
#123 retain their separate stale-handle and history guarantees.

## Acceptance and design

Validate the complete requested import against its target context before
publishing it, or provide an equivalent qualified transaction. Rejection must
retain the molecular system, semantic scene, live handles, undo/redo and queued
runtime state, including replacement/merge and conflict modes. Identity counters
must stay monotonic. Reconstructed objects that only look the same are not
preserved live handles.

Receive direct and file import, invalid later records, successful continuation,
named analyses and headless operation without copying the molecular trajectory
just for validation. A scene-only preflight must use the authoritative restore
path rather than maintaining a weaker duplicate validator. Runtime failures
after a valid import are a distinct boundary and must not inherit an unproved
universal transaction guarantee.

Original private evidence remains under E0. Source checkpoint at activation is
Viewer `8c594a3d5f5a9a9596640b8773e5373cf7ff32de`, with the local A4 correction.
