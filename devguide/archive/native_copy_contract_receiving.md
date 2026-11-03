---
summary: Qualify view and analysis independence against the native MolSysMT copy contract.
issue: uibcdf/molsysviewer#259
status: resolved
opened: 2026-10-21
closed: 2026-11-02
verification: measured
area: [molsysmt, interactions, state]
guard: tests/test_native_copy_receiving.py
normative: devguide/chemical_domain_receiving.md
blocked_by: []
supersedes: []
---

# Receive the native molecular copy and edit-ownership contract

## What

The provider notice requests consumer qualification when its complete-system
contract is ready. It does not report a reproduced failure of current public
Viewer copying and explicitly introduces no additional release blocker.
Coordination belongs to uibcdf/molsyssuite#122; provider implementation belongs
to uibcdf/molsysmt#121, which was open at the initial review and is now closed.

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
That checkpoint did not qualify complete molecular ownership or protected
coordinate editing in Viewer.

### Provider closure received — 2026-10-22

GitHub reports uibcdf/molsysmt#121 closed at `2026-10-22T20:15:56Z`.
The Studio inventory's later fixed source inspection includes public
`MolSys.copy(deep=…)` and its ownership contract, but no new consumer execution
or installed artifact receiving. Remove the upstream-open blocker and keep
this record open for qualification of the complete public boundary. Do not
infer Viewer recovery, cheap revisions or a new dependency floor from closure.

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

The upstream issue is closed; complete consumer receiving remains pending.
No provider API migration is authorized by this triage alone.


## Resolution — 2026-11-02

Viewer `481319a9a31af4dabe7482fdae0118752e229b91` receives the native
copy contract against MolSysMT `de7ffad2aef18ff3bccd184133dc69e081cb506e`
in the shared Python 3.14.7 environment. Five real pentalanine View guards pass
without skips. Coordinate edits use nonconsecutive source structures and unit
conversion; box and chemical-bond edits invalidate only the edited owner's
coverage. Changes in the opposite direction do not affect the copied geometry
or coverage. Old analysis/query handles remain historical results; nested
metadata and regions, annotations, shapes and interaction visibility remain
independent. An invalid coordinate write leaves geometry, current analysis and
coverage unchanged.

Copy followed by atom extraction and `[1, 0]` structure selection preserves
compound participants, parallel occurrences, periodic images, source maps,
producer metadata and units through an actual saved session. Existing
Interactions/session and scene-transfer guards also pass in the separate
265-case affected-source selection. This closes the source consumer
qualification requested here, without changing the `msm.copy` implementation
or adopting a deferred-copy optimization. A View copy does not promise a
particular allocation-sharing strategy.

The original failed prototype assertions during guard construction were
corrected against actual public annotation access and native exception types;
no runtime scientific assertion was weakened. The final five-case invocation
and original JUnit digest are recorded in
`devguide/chemical_domain_receiving_20261102.json`. Older public providers
without the protected-copy capability keep their independent compatibility
lane; all five cases must execute in designated new-source receiving.

This does not qualify an installed pair or clear #269. Its new exact-source
CI fails before scientific tests on all three platforms because the provider's
Rust export manifest omits `get_vectors`; evidence is handed to MolSysMT#255.
Public floors and installed/session/browser release receiving remain separate.
