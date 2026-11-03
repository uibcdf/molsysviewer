---
summary: Make JavaScript coverage measure executed production sources and reject empty LCOV.
issue: uibcdf/molsysviewer#290
status: resolved
opened: 2026-11-02
closed: 2026-11-03
verification: reproduced
severity: medium
area: [ci, coverage, testing]
guard: tests/test_js_source_coverage.py::test_real_production_functions_are_covered_and_unmapped_runner_is_rejected
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

The original bundle under `tests/unit` is discarded by c8's default exclusions
and has no source map. Adding a map and post-remap exclusions alone produces
another misleading result: every source line is hit but no functions are
measured. Node's coverage cache uses source-map file URLs, which the default
working-directory filter rejects while assigning function ranges. c8's
`allow-external` plus the source include pattern handles those names; the final
repository guard restricts accepted output to actual local production sources.

Receive coverage for actual executed production TypeScript sources, preserve
the complete JS selection and fail if the report lacks meaningful expected
source/line records. Do not instrument only a test wrapper or create artificial
LCOV entries. Qualify source maps/exclusions and the Node 22 hosted lane.
The advisory repair in #289 remains independent; no numerical coverage threshold
or runtime/scientific behavior was changed by that repair.

## Receiving — 2026-11-03

The complete unchanged index passes 335/335 cases on Node 22.22.1. The final
report contains 93 production sources: 28,347/42,599 lines (66.54%), 887/1,624
functions (54.61%) and 3,247/4,919 branches (66%). LCOV has 560,499 bytes.
These are standard V8 remapped unit-bundle measurements, not complete browser
or all-source coverage. No percentage threshold or dependency update is added.

Seven pytest guards pass with the real installed esbuild/c8: a production
local-UI-model probe has executed and unexecuted functions; its unmapped variant
is rejected. Missing/empty LCOV, harness-only attribution, the zero-function
false-full case and missing line records are also rejected. The full native
335-case run and the guard JUnit are retained in
`.pytest_cache/js-coverage-20261103/`.

CI runs the full JS selection and report validation immediately after JS
dependency installation, before Python tests, and preserves both reports. The
previous packaging/version-sync rebuild is removed from this unit-only step.
Exact-source hosted JS receiving is verified below. No tag, package or 1.0 claim.

## Resolution — 2026-11-03

Source `87de7eab2023c697a4de193fc2af6306fd0ee3f0` passes the hosted
“JS unit tests (Node)” and report-preservation steps in run 41667711689, job
126027409575. Downloaded original artifact 13247025814 has SHA-256
`91012f680f632b0b506f72294af2f71f70c9e6cc531402b5dcb9ed2e0715f44c`,
matching GitHub. Its LCOV is byte-identical to the measured local report; JSON
summary totals agree (absolute checkout paths account for different JSON bytes).
The enclosing Python matrix is still active at this observation; these passing
JS steps do not declare the overall workflow green. Hosted test stdout is not
yet available.

The seven real-tooling/negative guards protect attribution and rejection; the
371 integration checks pass at the source checkpoint after regenerating queue
indexes and staging new clean-checkout link targets. The final archived-state
selection passes 368 cases; three open-queue parameterizations disappear. The
[receipt](../js_source_coverage_receiving_20261103.json) retains local and hosted
identities, hashes, counts and limitations. The normative coverage rule is in
[the dependency contract](../dependency_contract.md#javascript-registry-advisories);
[developer testing](../../docs/content/developer/testing.md) explains execution.
No production runtime, lockfile, numerical acceptance threshold or public
artifact changes. Provider receiving under #269 and addon #264 remain separate.

## Later hosted observation — 2026-11-03

The completed Linux job log confirms Node 22.23.4 and 335/335 JS cases. The
enclosing Python job fails exactly the three previously identified old-provider
Pandas4Warning documentation examples. Original JUnit from source run
41667711485 verifies all seven report controls passing separately on Linux,
macOS and Windows; that run uses the old provider source, not the newly received
chemical-domain source. Policy run 41667713327 separately rejects formatting in
the new Python test. Its formatter-only correction preserves all assertions;
seven directed controls pass afterward. The follow-up source/CI disposition is
kept in [the receiving receipt](../chemical_domain_receiving_20261103.json).
