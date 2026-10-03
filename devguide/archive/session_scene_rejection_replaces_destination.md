---
summary: Rejected session scenes replace the destination system and erase open work.
issue: uibcdf/molsysviewer#127
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: high
verification: reproduced
area: [state, persistence]
guard: tests/test_session_rejection.py
normative:
blocked_by: []
supersedes: []
---

# Rejected session scenes replace the destination

**Reported:** 2026-10-01, while reviewing the implementation of the remaining
public persistence promises before the final documentation pass.

## What

Changing only `state.json`'s version to 999 in a real dialanine session and
loading it onto a pentalanine view raises `Unsupported state version`, but
changes the destination molecular system and removes its annotations.

```python
msv.load_session(path_to_session_with_invalid_scene, view=destination)
```

The destination's system identity, scene, handles, undo/redo and outgoing
replay must survive rejection of invalid saved scene data.

## How

`session.load_session` validates scientific manifest signatures before loading,
but calls `load(..., mode="replace")` before `import_state`. State validation
and overlay restoration failures happen after the destination has been reset.

Validate restoration of the complete incoming scene on an isolated, temporary
view before replacing an existing destination. Use the public system-edit
primitive with `interactions_policy="preserve"` to borrow the already read
MolSys: preflight must not duplicate the complete trajectory. The temporary
view owns its scene and widgets, and is closed on both success and failure.
Its scientific data are read-only during restoration. A newly allocated
destination also needs explicit cleanup if its restoration fails.

## Why

Reopening a portable session must not erase open work because the stored scene
is invalid. Existing tests only protect scientific manifest rejection; valid
scientific data do not prove the scene can be restored.

## What was refuted

- Checking only state version is insufficient: dependency graphs, scientific
  display references and clipping-plane parameters fail later.
- Reimplementing scene validation in the session reader would create a second
  schema and miss future restoration checks. Preflight executes `import_state`.
- Loading a second copy of the trajectory for scene validation would worsen
  the memory cost of an already materialized session. Borrowing the incoming
  MolSys through `apply_system_edit` avoids that copy.

This is a guard against invalid persisted data, not a transaction covering
arbitrary transport failures or allocation failures during destination commit.

## Resolution

Implemented on 2026-10-01. `_validate_session_scene` restores the complete
incoming scene on a temporary view borrowing the loaded MolSys through
`apply_system_edit(..., interactions_policy="preserve")`. The context manager
closes its widgets even when the importer raises. An existing destination is
replaced only after that restoration succeeds. Failed restoration of a newly
allocated destination explicitly closes it.

`tests/test_session_rejection.py` covers unsupported versions, cyclic and
missing region operands, and invalid clipping planes with and without a reused
destination. It asserts system identity, unchanged coordinates in nm, exact
scene, current handle identity, undo/redo, annotation replay and molecular
projection, plus unchanged widget registry membership. A successful reused
load also asserts replacement and widget cleanup.
`tests/test_interactions_scene.py::test_session_rejects_invalid_scientific_scene_before_replacing_destination`
adds mismatched analysis references, incompatible radius units, invalid frame
filters and unsupported scientific scene versions with a valid H5MSM analysis.

Validation: the new file passes 9 tests, and the affected scientific/session/
lifecycle selection passes 69 tests. A single complete Python 3.14 run passes
**2,313 tests, 20 skipped, no failures**, exit 0 in 287.11 seconds. Its log is
`/tmp/msv-session-full-20261001.log`. Ruff and `git diff --check` pass. The
provider remained at `18cc43021a663b5c79b8aa7b51cdef5e1fe27785`, with its
independently dirty working tree preserved; this is development-checkout
evidence, not installed-release qualification. No TypeScript changed.

All three guards were removed separately and the focused test failed each
time: omitting preflight changes the system identity, omitting temporary-view
closure leaks two widgets, and omitting newly allocated destination closure
also leaks two widgets. Each mutation restored the exact original source bytes.
Logs: `/tmp/msv-session-mutation-{preflight,temporary_cleanup,new_view_cleanup}-20261001.log`.
The session format remains experimental; this fix establishes no new migration
or archival compatibility promise.
