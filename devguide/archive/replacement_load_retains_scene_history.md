---
summary: Successful replacement loading retains scene history from the previous system.
issue: uibcdf/molsysviewer#262
status: resolved
opened: 2026-10-22
closed: 2026-10-22
severity: medium
verification: reproduced
area: [history, loading]
guard: tests/test_load_history_boundary.py
normative:
blocked_by: []
supersedes: []
---

# Successful replacement loading retains the previous scene history

**Reported:** 2026-10-22 during the molecular integration audit; reproduced
after the maintainer authorized proceeding with the integration design.

## What

Successful `load(mode="replace")` removes the current scene objects but leaves
their scene-only Undo history. Undo can restore an old annotation over the
replacement MolSys, without restoring the previous molecular system.

```python
import molsysmt as msm
import molsysviewer as msv

with msv.demo["dialanine"] as view:
    view.annotations.add("before", atom_indices=[0], tag="audit-note")
    view.annotations.set_text("audit-note", "edited")
    candidate = msm.copy(view.molsys)
    view.load(candidate, mode="replace")
    print(view.annotations.count(), view.history.can_undo())  # 0, True
    print(view.history.undo())                               # True
    print(view.annotations.info("audit-note")["text"])        # before
```

Reproduction used Viewer source `d96b073f23247e25cd42c95af545b6d20e7fa982`
and `/home/diego/Myopt/miniconda3/envs/molsyssuite@uibcdf_3.14/bin/python`
(Python 3.14.7). Viewer and MolSysMT imports resolve to the local checkouts.
MolSysMT's distribution reports `0.23.0+93.g48aba006f`; this metadata is not
asserted to identify a frozen source or installed artifact. No browser or
scientific qualification is claimed. Loading the bundled demo emitted the
existing H5MSM 0.4 deprecation warning, unrelated to history behavior.

## How

`viewer/load.py:369` uses `_reset_viewer(awaiting_structure=True)` and
`_commit_molsysmt_load` for successful replacement. Neither clears the
`SceneHistory` Undo/Redo stacks. Resetting shape/annotation replay records and
retiring objects is a different responsibility.

`viewer/core.py:2424` explicitly clears history during
`_rebuild_view_from_current_molsys`, used by additive loading and
`apply_system_edit`. `SceneHistory` documents load/edit invalidation because its
snapshots do not retain molecular data. Its ordinary restore can therefore
replay an older scene without performing molecular Undo.

## Why

Users can invoke Undo after replacing molecular content and resurrect objects
belonging to previous work. The current scene-only history must enforce its
declared molecular replacement boundary until complete recovery is deliberately
implemented. The future design must restore coherent molecular and scene state
instead of accidentally preserving this behavior.

## What was refuted

- Scene replay cleanup alone does not clear Undo/Redo; reproduction restores
  the old annotation after the replacement removed it.
- Closed uibcdf/molsysviewer#148 and #157 concern rejected/preparation-failed
  replacements. This case is a successful replacement with valid matching
  topology; those guards do not cover it.
- This does not demonstrate failure of MolSysMT copying or molecular Undo: the
  former completes and the latter is not implemented by scene snapshots.

## Resolution

`_reset_viewer` now clears the scene-only Undo/Redo store when it retires the
scene. `_commit_molsysmt_load` also clears it when adopting the prepared MolSys,
covering the first molecular load into a shape-only view without removing its
existing geometry. Both use the existing `SceneHistory.clear` owner, including
the frontend availability update. Source preparation and composition still
precede these boundaries, so rejected inputs preserve both stacks.

`tests/test_load_history_boundary.py` uses the real bundled dialanine system.
Its 10 cases cover single and batch replacements with both digestion settings,
matching topology, old annotations that cannot reappear, rejected single and
later batch sources with exact Undo/Redo preservation, explicit reset followed
by loading, and a first molecular load retaining a caller sphere. New scene
operations remain undoable after successful loading. The shape-only guard
reacquires its handle after its preparatory Undo, respecting the existing
retired-handle contract; the initial test attempt incorrectly reused that
retired handle and was corrected before the passing run.

Focused validation: 10 passed in the explicit Python 3.14 development
environment. The once-run full core suite (`-m 'not qt_runtime' -n 8`) returned
3,230 passed, 21 skipped and two failures; it is not a passing full-suite gate.
One failure is the pre-existing box-test setup tracked in
uibcdf/molsysviewer#263. It was reproduced on clean baseline
`d96b073f23247e25cd42c95af545b6d20e7fa982`: the test's own initial box assignment
invalidates its already attached analysis before the partial edit under test.
The other failure is the clean-checkout link guard observing local untracked
planning documents (and the not-yet-staged new closure record). Those planning
files are preserved separately from this fix. Applying only the six staged fix
files to the clean baseline and running the regression, devguide-link and
reporting-protocol modules passed 283 tests. This confirms the closure record
and its links are self-contained without the unrelated planning files. Local
JUnit: `/tmp/molsysviewer-262-core.xml` and
`/tmp/molsysviewer-262-isolated.xml` (not portable publication receipts).
The bundled demo's H5MSM 0.4 deprecation warnings remain
unrelated. This restores the current scene-only contract; it does not implement
molecular Undo or automatic linked editing.
