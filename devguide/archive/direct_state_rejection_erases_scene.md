---
summary: Rejected direct state imports erase existing scene objects before validation finishes.
issue: uibcdf/molsysviewer#317
status: resolved
opened: 2026-11-06
closed: 2026-11-16
severity: high
verification: reproduced
area: [state, history, lifecycle]
guard: tests/test_state_rejection.py::test_rejected_state_preserves_live_scene_history_and_resources
normative:
blocked_by: []
supersedes: []
---

# Direct state rejection erases open work

## Source resolution — consolidated receiving, 2026-11-16

State candidates validate before publication. The guard checks rejected direct/file and clear/merge paths against the existing scene, history, handles, molecular data and independent resources.

The complete source checkpoint
[43748320908](https://github.com/uibcdf/molsysviewer/actions/runs/43748320908)
receives MolSysViewer `3aff1d48a5a38fb9854efe2c95a9a8f35cadbccb` and
MolSysMT `bc5a9297a762d451742734f9e11c7f54c6a832a0`. The durable guard
is `tests/test_state_rejection.py::test_rejected_state_preserves_live_scene_history_and_resources`.
Its containing module passes **32 cases on each of Linux, macOS arm64
and Windows**, without failures, errors or skips. The [closing receipt](../molstar_closeout_three_blocks_20261115.json)
checks original JUnit ZIP digests and native selected cases; the complete
checkpoint also receives all 25 notebooks.

This supplies the formerly pending consolidated **source** prerequisite.
Earlier causal runs, interrupted/failed receiving and dated pending claims
remain below with their original inputs. Installed artifacts, final producers,
experimental native Qt and postponed human acceptance retain their own owners
and gates under #315/#372; this closure does not declare them passed or
advance the original 40/46 source or 1/46 final-acceptance counters.

## Earlier investigation — original claims and scopes retained


**A2 — implemented/source-verified; hosted receiving pending; P1.** Viewer
owns #317 under #315, for the covering artifact and accepted 1.0 scope. Directed
guards and the final 180-case combined selection pass. Source delivery
accompanies this record; applicable hosted receiving remains the next gate.
No provider fix is needed.

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

## Correction and receiving

Public import now invokes the same authoritative restoration code on an
isolated View that borrows the current molecular system and receives the
destination's scene. Only after that succeeds does the destination restore the
request. Merge and conflict semantics therefore use the actual target context;
failed validation does not reconstruct or retire its existing live handles.
The session validator reuses that private restore path on its already isolated
owner without nesting another preflight.

The destination contributes one scene snapshot and its current, read-only
scientific identity/binding caches. An unchanged trajectory is not rehashed for
each candidate. Real pentalanine/dialanine receiving checks reuse and explicit
replacement invalidation. Existing announced-edit cache rules still apply;
this does not add automatic observation of raw MolSys edits.

The causal red guard observes scene changes after rejecting a later section.
An earlier fixture setup error lacked explicit shape units and is not causal
product evidence. The 24-way direct/file, clear/merge and conflict matrix then
passes after correction. Further guards cover fatal/new versus already accepted
overlap diagnostics and cached scientific correspondence, bringing the directed
file to 29 passing cases. Import phases are per-View; diagnostic policy is not
reconfigured globally, old overlap warnings are not replayed as new requests,
and successful publication does not duplicate those warnings.

The first broad attempt retains 164 passes and one failure: its old history
guard counted the new explicit validation snapshot as an unwanted checkpoint.
The strengthened guard receives one explicit snapshot for both one and twelve
regions and no checkpoints during rebuilding. The subsequent 166- and 176-case
selections pass on their respective inputs. A final combined run after binding
cache reuse and three additional actual-target conflict cases passes all 180
cases in 61.50 s, with selected sources/tests and native binaries unchanged.
The [receipt](../state_import_rejection_receiving_20261106.json)
retains source hashes, actual commands, warnings and limits. These overlapping
counts are not one summed total.

E0's approved custody is now received in
[its verification record](../robustness_evidence_custody_20261106.json). The
programme and this source correction remain open for their remaining acceptance.
