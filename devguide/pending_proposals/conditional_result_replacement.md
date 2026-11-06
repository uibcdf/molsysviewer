---
summary: Condition replacement on the reviewed molecular target and revision.
issue: uibcdf/molsysviewer#306
status: partial
opened: 2026-11-06
closed:
verification: inspected
area: [addons, editing, api]
guard: tests/test_conditional_system_replacement.py
normative: docs/content/developer/addons.md
blocked_by: []
supersedes: []
---

# Conditional independent-result adoption

## What

The accepted task design includes explicit Use in this view for independent
preparation outputs. The existing serialized replace operation is unconditional;
a caller-side review check followed by replace can overwrite intervening work.
The read callback explicitly prohibits writes, so it cannot be repurposed as a
hidden replacement transaction. The complete 304-record inventory includes
related #301 presentation and #264 addon receiving, with no conditional service.

## How

Extend the existing headless replacement with keyword-only expected_target and
expected_revision. A nonnegative revision enables the exact identity/revision
check inside the same lock as load. None can identify an expected empty target.
Without a revision, a nonempty expected target is invalid; the original
unconditional recovery contract remains available. Stale, uncertain, busy and
closed cases reject before changing data/scene/history/revision. Semantic
preconditions remain active when digestion is skipped.

The host does not copy results, calculate chemistry, authenticate source IDs,
observe raw arrays or promise rollback of a subsequent failed native load.
Providers own scientific output, independent copying, explicit replacement
consent and bounded single-use review state. Existing scene-reset semantics
remain explicit. Source support does not qualify public packages or a release.

## Verification

Implementation is received in an isolated host worktree. Thirty-three new
demo/concurrency cases pass inside a 72-case managed-edit/reader/endpoint
regression. Fifty-three public digestion/inventory/docs/caller cases pass. The
closed inventory retains all 736 public callables digested, no missing
validators, and exactly two new declared validators (450 total). The
[receipt](../conditional_result_replacement_receiving_20261106.json) preserves
initial import/fixture/inventory failures and their bounded corrections.
Exact-head hosted/consumer/installed and postponed human qualification remain
separate; keep the report partial until required integration is verified. The earlier complete 4,699-case addon result
uses unchanged Viewer 2e17ee6f and does not qualify this new host slice.
