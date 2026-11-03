---
summary: Make JavaScript coverage measure executed production sources and reject empty LCOV.
issue: uibcdf/molsysviewer#290
status: open
opened: 2026-11-02
closed:
verification: reproduced
severity: medium
area: [ci, coverage, testing]
guard:
normative:
blocked_by: []
supersedes: []
---

# Empty JavaScript source coverage

`npm run coverage:js` succeeds while `coverage-js/lcov.info` is empty. Native
Node 22 executes all 334 original cases; after #289, those same cases and a new
real-tooling test pass (335 total). Before/after LCOV remains zero bytes with no
SF/LF/FNF/BRF records. Actual test execution remains evidence; source coverage
does not. The original reports are retained in the source receiving receipt.

Inspect c8's default exclusions and the esbuild runner under `tests/unit`.
Current test bundling does not request source maps. The current evidence
supports this as a suspected mapping/filter boundary, not a proven remedy.

Receive coverage for actual executed production TypeScript sources, preserve
the complete JS selection and fail if the report lacks meaningful expected
source/line records. Do not instrument only a test wrapper or create artificial
LCOV entries. Qualify source maps/exclusions and the Node 22 hosted lane.
The advisory repair in #289 remains independent; no numerical coverage threshold
or runtime/scientific behavior was changed by that repair.
