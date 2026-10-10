---
summary: Empty dynamic region disappears during state restoration on macOS Python 3.12
issue: uibcdf/molsysviewer#189
status: active
opened: 2026-10-09
closed:
severity: medium
verification: upstream
area: [regions, state, tests]
guard:
normative:
blocked_by: []
supersedes: []
---

# Empty dynamic region disappears during state restoration on macOS Python 3.12

**Reported:** 2026-10-09, inspecting the prior checkpoint's hosted CI during
the Studio round.

## What

CI `37993286215`, source `84a2a75dde3a4292d5bebb2e4c4dfa41c4d56568`, fails
`tests/test_region_isolation.py::test_empty_dynamic_isolation_survives_restore_and_rebuild_then_reappears`
on macOS/Python 3.12. `view.regions["near"]` raises `KeyError` at line 155,
immediately after the real dialanine view imports its own exported state.
The cell reports 2,883 passed, 62 skipped, one failed. The other five scientific
CI cells pass. The separate experimental Qt failure is unrelated evidence.

```bash
python -m pytest tests/test_region_isolation.py::test_empty_dynamic_isolation_survives_restore_and_rebuild_then_reappears -x -q
```

The case isolates a dynamic distance-query region, moves its atom far away,
and checks empty isolation through state/session/copy/system-edit recovery and
subsequent reappearance.

## How

The root cause is not established. State restoration already has an explicit
empty dynamic-recipe path. The old compact CI diagnostic does not expose the
serialized mode/provenance; the existing guard now reports the bounded region
records if the region disappears. Inspect the next exact-source macOS result
before deciding whether importer, provider or test isolation needs correction.

## Why

A valid empty evaluated structure must not erase a dynamic region's recipe or
its isolation state. This observation must be reconciled before final 1.0
source clearance.

## What was refuted

Passing Linux source tests does not establish the cause of a macOS failure.
This report is not a reason to skip the guard, silently discard the region,
or substitute the unrelated Qt/WebGL result.

## Resolution

Diagnosis and exact-source macOS verification pending. Original failure remains
at https://github.com/uibcdf/molsysviewer/actions/runs/37993286215.

## Follow-up — 2026-10-10

Base-source a699f5b5 run 38034284564 completes all six scientific cells
successfully, including macOS/Python 3.12. Its separate experimental Qt job
fails. The later macOS success is recorded without attributing a cause to the
historical disappearing-region failure; no guard was skipped or replaced.
Diagnosis remains open.
