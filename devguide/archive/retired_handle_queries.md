---
summary: Retired region and layer handles must reject read operations
issue: uibcdf/molsysviewer#219
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [public-api, scene]
guard: tests/test_public_api_followup.py::test_retired_queries_reject_tag_reuse_without_changing_state
normative:
blocked_by: []
supersedes: []
---

# Retired region and layer handles must reject read operations

**Reported:** 2026-10-10, final API review with real dialanine systems.

## What

After deletion and tag reuse, old Region.select/get/get_center still query old atoms and old Layer.info reports replacement members.

## How

Apply the existing current-handle check to public molecular queries and layer membership reads. Implementation owner: `molsysviewer/regions.py and molsysviewer/layers.py`.

## Why

Public queries, history and introspection must agree with scene contracts before 1.0.

## What was refuted

Provider atom-scoped system queries work; this is Viewer ownership/delegation. Existing mutation guards do not protect undecorated read paths. No package qualification or scientific stability claim follows from these local checks.

## Resolution

Implemented the public boundary in molsysviewer/regions.py and molsysviewer/layers.py. Guard `tests/test_public_api_followup.py::test_retired_queries_reject_tag_reuse_without_changing_state` passes on real dialanine data. The complete related execution passes 310 cases. The single full run reports 3056 passed, 9 failed and 23 skipped; eight failures are known experimental Qt host probes, and the ninth is the superseded whole-system count test. After updating that policy assertion, its tools module passes 14 cases. No second full execution or globally green claim. The source follow-up and receipt retain the evidence; 0.25.0 remains unfrozen and publication paused.
