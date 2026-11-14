---
summary: Read periodic cells through their provider instead of its old private store.
issue: uibcdf/molsysviewer#390
status: resolved
opened: 2026-11-14
closed: 2026-11-14
severity: medium
verification: measured
area: [testing, periodicity, dependencies, qualification]
guard: molsysviewer/js/tests/e2e/coordinate-edits.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Native symmetry receiving provider

Run `43627876434` on `1a8d630d` and scientific source `aee7aa65` receives
15 complete core suites, then fails the cell-size comparison in coordinate
editing: `actual.size` is null. Its helper named `close` compares numbers;
this is not a cleanup exception. The run remains failed.

Three assertions directly read `_staticPropertyData.model_symmetry`.
Native 5.13.1 creates `ModelSymmetry.Provider` with `asDynamic=true` and
`cachePerFormat=true`. Use its public getter from the same native module
as the harness. Preserve exact lengths, nonorthogonal angles, frame
coordinates, box geometry and removal/placeholder assertions. Receive
the real fixture before concluding that this is only a stale guard: the null
private-store value alone does not establish loss of the molecular box.

The complete four-page, 359-issue history has no equivalent report. This is
separate from #388/#389's picking and #244's aggregate receiving budget.

## Source resolution — 2026-11-14

All three reads now call `ModelSymmetry.Provider.get(model)` in the actual
native harness. Profile `822` passes the complete coordinate-edit suite:
all submitted cell lengths/nonorthogonal angles and three-frame coordinates,
box geometry/removal, both managed edit readers, mounted-DOM recovery, real
centroid measurements, saved work and bidirectional popup frame mirroring.
The original numeric tolerances and expected cells are unchanged. This
receives the stale-private-reader diagnosis; it does not infer lost box data
from the old null value. Build/type and scoped guards pass in `818`.

The exact hosted run remains failed, with 15/62 complete browser suites,
4,731 Python passes/42 skips/17 deselections and all 25 notebooks passing.
Its two original artifact ZIPs have independently verified sizes/digests.
The next full core gate still belongs to #372.
