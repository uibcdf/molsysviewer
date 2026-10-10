---
summary: Region.get system queries must stay inside the region
issue: uibcdf/molsysviewer#218
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: high
verification: reproduced
area: [public-api, scene]
guard: tests/test_public_api_followup.py::test_region_system_queries_never_expand_atom_scope
normative:
blocked_by: []
supersedes: []
---

# Region.get system queries must stay inside the region

**Reported:** 2026-10-10, final API review with real dialanine systems.

## What

Region.get(n_atoms=True) on dialanine region [0,1] returns 22 instead of 2; selection=[10] returns an outside atom. Native MolSysMT scoped get returns 2.

## How

Resolve default system queries through the region atom scope while preserving global structural attributes. Implementation owner: `molsysviewer/regions.py`.

## Why

Public queries, history and introspection must agree with scene contracts before 1.0.

## What was refuted

Provider atom-scoped system queries work. An older tools test deliberately pinned whole-system counts; this authorized pre-1.0 scope decision supersedes that test policy. Global structural attributes remain provider-owned. Existing mutation guards do not protect undecorated read paths. No package qualification or scientific stability claim follows from these local checks.

## Resolution

Implemented the public boundary in molsysviewer/regions.py. Guard `tests/test_public_api_followup.py::test_region_system_queries_never_expand_atom_scope` passes on real dialanine data. The complete related execution passes 310 cases. The single full run reports 3056 passed, 9 failed and 23 skipped; eight failures are known experimental Qt host probes, and the ninth is the superseded whole-system count test. After updating that policy assertion, its tools module passes 14 cases. No second full execution or globally green claim. The source follow-up and receipt retain the evidence; 0.25.0 remains unfrozen and publication paused.
