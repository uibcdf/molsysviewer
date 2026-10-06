---
summary: GroupPanel unit DOM fixture lacks querySelector required by Interactions
issue: uibcdf/molsysviewer#166
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [testing, ui, interactions]
guard: molsysviewer/js/tests/unit/group-panel.test.ts
normative:
blocked_by: []
supersedes: []
---

# GroupPanel unit DOM fixture lacks querySelector required by Interactions

**Reported:** 2026-10-06 during regression verification of #164 and #165.

## What

From `molsysviewer/js`, `npm run test:js` exits 1. GroupPanel construction
fails with `TypeError: scope.querySelector is not a function` in
`InteractionsPanel.paint`, before the GroupPanel assertions execute.

## How

`tests/unit/group-panel.test.ts::FakeElement` implements a small DOM subset
without `querySelector`. `src/ui/panels/interactions-panel.ts` now calls that
method to disable the `between` option for the disulfide candidate family.
Those two files are unchanged by #164/#165; source inspection identifies a
pre-existing fixture incompatibility. The command output also reports the
failure in multiple GroupPanel cases. The complete unit lane has not been
shown clean and should be captured to a durable log during the correction.

Update the owning test fixture to implement the actual browser operations
used, with selector behavior that can still expose wrong selectors. Inspect
the subsequent complete trace before claiming this is the only unit defect.

## Why

The advertised unit lane must pass before 1.0 and provide usable regression
evidence. The missing test DOM method makes unrelated panels appear broken.

## What was refuted

This failure does not establish a missing browser API or failed molecular
loading. Real Chromium composite loading, Studio loading, array-native
transport and panel-popup tests pass. No runtime fallback or scientific
provider change is justified by this trace.

## Resolution

The fixture now preserves element tags/option values, resolves scoped descendant
selectors and implements prepend ordering. Missing options return null; wrong
selectors cannot silently resolve to an arbitrary option. The regression
`GroupPanel test DOM resolves scoped options and preserves prepend order`
guards this behavior, and GroupPanel construction exercises the actual
InteractionsPanel selector. Runtime Interactions code is unchanged.

The unsandboxed complete pre-fix trace has 287 passed and 33 failed, all with
the missing querySelector cause. The focused owner passes 35 tests and the
final complete JS unit lane passes 322 tests, zero failures/skips. The initial
sandboxed Node child emitted only a generic failed-file result; the subsequent
unsandboxed trace is the diagnosis evidence. The bounded unit guard profile is
declared in `devguide/reporting_protocol.md` and checked by the local validator.
See `devguide/region_enablement_20261006.json` for retained validation scope.
