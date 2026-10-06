---
summary: Interactions materialization guard counts unrelated decorator calls
issue: uibcdf/molsysviewer#162
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [testing, interactions, performance]
guard: tests/test_interactions_scene.py::test_oversized_frame_is_refused_before_occurrence_materialization
normative:
blocked_by: []
supersedes: []
---

# Interactions materialization guard counts unrelated decorator calls

**Reported:** 2026-10-06 from the once-run complete source regression after
qualifying the current scientific provider: 2,820 passed, 23 skipped, one failure.

## What

`tests/test_interactions_scene.py::test_oversized_frame_is_refused_before_occurrence_materialization`
counts 235 `wrapper` calls and fails its no-full-materialization assertion.

## How

The profiler compares `frame.f_code` against the decorated
`molsysmt.Interactions.to_dict.__code__`. That code belongs to SMonitor's shared
decorator and is also used by `Interactions.query`, among other public methods.
The guard therefore treats unrelated calls as full occurrence serialization.

Unwrap the actual serializer, preserving any existing profiler. Before the
bounded 50,001-occurrence frame path, serialize the small real provider result
and assert the observer records exactly that concrete call. Clear the observation
and retain the zero-materialization assertion for rendering and paged inspection.

## Why

Large sparse analyses need a guard that detects real full-column copying. Shared
public decorators must not cause false positives or an observer that sees nothing.

## What was refuted

The failure does not establish that rendering copied 50,001 occurrences. Its
observer identifies a shared wrapper rather than the serializer implementation.
The actual provider pager remains bounded; verification must retain the render
limit, total occurrence count, 50-row page and next-offset assertions.

## Resolution

The guard now targets `inspect.unwrap(Interactions.to_dict).__code__`, chains
any prior profiler and verifies its positive control with a real small query
serialization. The full 22-case scene module passes in 13.85 s in
`molsyssuite@uibcdf_3.14`. Its large-frame path records zero concrete serializer
calls while retaining the render refusal, 50-row inspection page and next-offset
assertions. This protects both observer correctness and the bounded consumer path.

The preceding complete run remains 2,820 passed, 23 skipped and one failed
guard. It was not repeated; this correction has focused evidence, not a new
clean full-suite or hosted certificate. See
[the retained receipt](../ci_environment_repair_20261006.json).
