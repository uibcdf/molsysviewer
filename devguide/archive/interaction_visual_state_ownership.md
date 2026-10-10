---
summary: Protect InteractionSet filters and styles through detached properties
issue: uibcdf/molsysviewer#222
status: resolved
opened: 2026-10-10
closed: 2026-10-10
verification: reproduced
area: [public-api, scene]
guard: tests/test_public_api_followup.py::test_interaction_state_reads_are_detached_and_setters_own_history
normative:
blocked_by: []
supersedes: []
---

# Protect InteractionSet filters and styles through detached properties

**Reported:** 2026-10-10, final API review with real dialanine systems.

## What

InteractionSet.filter/style expose live mutable dictionaries, allowing changes outside validation and scene history.

## How

Expose detached read-only properties, retain explicit setters, and use private backing state for internal frame queries and remapping. Implementation owner: `molsysviewer/interactions.py, viewer/core.py and viewer/state.py`.

## Why

Public queries, history and introspection must agree with scene contracts before 1.0.

## What was refuted

Provider atom-scoped system queries work; this is Viewer ownership/delegation. Existing mutation guards do not protect undecorated read paths. No package qualification or scientific stability claim follows from these local checks.

## Resolution

Implemented the public boundary in molsysviewer/interactions.py, viewer/core.py and viewer/state.py. Guard `tests/test_public_api_followup.py::test_interaction_state_reads_are_detached_and_setters_own_history` passes on real dialanine data. The complete related execution passes 310 cases. The single full run reports 3056 passed, 9 failed and 23 skipped; eight failures are known experimental Qt host probes, and the ninth is the superseded whole-system count test. After updating that policy assertion, its tools module passes 14 cases. No second full execution or globally green claim. The source follow-up and receipt retain the evidence; 0.25.0 remains unfrozen and publication paused.
