---
summary: Qualify view and analysis independence against the native MolSysMT copy contract.
issue: uibcdf/molsysviewer#259
status: blocked
opened: 2026-10-21
closed:
verification: inspected
area: [molsysmt, interactions, state]
guard:
normative:
blocked_by: [uibcdf/molsysmt#121]
supersedes: []
---

# Receive the native molecular copy and edit-ownership contract

## What

The provider notice requests consumer qualification when its complete-system
contract is ready. It does not report a reproduced failure of current public
Viewer copying and explicitly introduces no additional release blocker.
Coordination belongs to uibcdf/molsyssuite#122; provider implementation belongs
to uibcdf/molsysmt#121, still open at this review.

## How

`molsysviewer/tools/basic/copy.py` currently calls public `msm.copy(view._molsys)`
before transferring detached scene state. It does not call Python's
`copy.copy(MolSys)` or an unpublished complete-system deferred-copy API.
`tests/test_tools_basic.py::test_tools_basic_copy_returns_independent_view_with_scene_state`
guards separate Viewer/MolSys objects and retained scene state; it does not
prove the future complete coordinate/analysis edit-ownership contract.

MolSysMT reports `85b8b038008de4b6ac05e6f6c3e5028935bd3f85` as an analysis-only
`Interactions.copy()` checkpoint. Its reported immutable-byte sharing, metadata
isolation and raw-column/deep-copy memo limitation remain provider assertions
here, not a locally executed qualification or a new published dependency floor.
Complete molecular ownership and protected coordinate editing remain pending.

When ready, receive an exact provider source/version and qualify:

- Molecular and named-analysis edits in both directions, with prior handles
  retaining valid snapshots and failed edits leaving prior state intact.
- Atom/structure axes, units, explicit live-reference operations and affected
  structure coverage/cache invalidation, without invalidating the other copy.
- Occurrence references, query order, evaluated-empty coverage, compound roles,
  images, source maps and original producer provenance through sessions/H5MSM.
- View-owned visual state, regions, annotations, shapes and interaction display,
  independently of provider storage sharing.

Keep regression guards in the existing basic-tools and Interactions/session
owners. Public package or browser qualification must be received separately;
provider unit tests cannot certify those consumers.

## Why

Sparse analyses should not require serializing every observation merely to copy
a view. Storage sharing is acceptable only with explicit independent-edit
guarantees. This review changes no runtime, public dependency minimum or copy
promise, and does not delay documentation or freeze by itself.

## Resolution

Waiting for the complete provider boundary. No provider API migration is
authorized by this triage alone.
