---
summary: Studio creation loses drafts and can attach members after a rejected layer creation
issue: uibcdf/molsysviewer#201
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: high
verification: reproduced
area: [studio, frontend]
guard: molsysviewer/js/tests/e2e/studio-list-workflows.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Studio final review — creation

**Reported:** 2026-10-10, final Studio review with real pentalanine and Mol*/Chromium.

## What
Measures clears the name and staged selections before receiving Python success; Annotations also clears creation text and anchor prematurely. Layers sends create_layer and each membership change independently: a duplicate name rejects creation, but following requests attach members to the existing layer.

## How
Reproduced in the final Studio review with real pentalanine/Mol* and isolated Python dispatch. Measures emits a duplicate measurement tag and immediately empties its form; Python rejects that tag. Creating an existing layer raises ValueError; the next add_member_to_layer request still changes that layer.

## Why
A rejected operation must preserve the user's work and must not modify an existing scene object. Before 1.0, extend correlated Studio creation results, preserve drafts until success, prevent pending duplicates, and make layer creation with initial members atomic. Add real browser/backend guards.

## What was refuted

Embedded snapshots intentionally omit live editing flags. The browser fixture now uses real runtime summaries and explicitly projects them after frame navigation, so draft checks exercise actual repaints.

## Resolution

Correlated CreationFeedback keeps Measures/Annotations/Layers drafts until success and locks pending controls. Python assigns the result domain. Layers sends one request with all initial members; validation precedes mutation and existing owner operations share an atomic history boundary. Real browser duplicate-measurement/layer failure and recovery, exactly one layer request, pending duplicate prevention, annotation success, and one-step layer Undo/Redo pass. tests/test_studio_creation_feedback.py adds backend state/redo preservation, complete member prevalidation, mixed-member Undo/Redo and correlated domain checks.

**Executed:** 14/14 focused Python cases; TypeScript no-emit check; npm JS unit suite; real pentalanine/Mol*/Chromium Studio guard. These are source/development checks, not installed artifact qualification. The complete Python run and hosted gates retain their separate outcomes.
