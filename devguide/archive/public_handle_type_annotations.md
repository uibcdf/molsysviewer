---
summary: Public handle annotations must match runtime return types
issue: uibcdf/molsysviewer#221
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: low
verification: reproduced
area: [public-api, scene]
guard: tests/test_public_api_followup.py::test_public_handle_annotations_match_runtime_objects
normative:
blocked_by: []
supersedes: []
---

# Public handle annotations must match runtime return types

**Reported:** 2026-10-10, final API review with real dialanine systems.

## What

Annotation and measurement managers declare Layer returns but return sibling Annotation/Measurement handles. typing.get_type_hints(Layer.attach/detach) fails because Region is absent from runtime globals.

## How

Correct the owner return annotations and resolve membership type hints at runtime. Implementation owner: `molsysviewer/annotations.py, measurements.py and layers.py`.

## Why

Public queries, history and introspection must agree with scene contracts before 1.0.

## What was refuted

Provider atom-scoped system queries work; this is Viewer ownership/delegation. Existing mutation guards do not protect undecorated read paths. No package qualification or scientific stability claim follows from these local checks.

## Resolution

Implemented the public boundary in molsysviewer/annotations.py, measurements.py and layers.py. Guard `tests/test_public_api_followup.py::test_public_handle_annotations_match_runtime_objects` passes on real dialanine data. The complete related execution passes 310 cases. The single full run reports 3056 passed, 9 failed and 23 skipped; eight failures are known experimental Qt host probes, and the ninth is the superseded whole-system count test. After updating that policy assertion, its tools module passes 14 cases. No second full execution or globally green claim. The source follow-up and receipt retain the evidence; 0.25.0 remains unfrozen and publication paused.
