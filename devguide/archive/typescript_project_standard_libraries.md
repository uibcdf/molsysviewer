---
summary: Standard TypeScript project checks omit libraries used by Movie.
issue: uibcdf/molsysviewer#371
status: resolved
opened: 2026-11-12
closed: 2026-11-12
severity: medium
verification: reproduced
area: [build, typescript, configuration]
guard: tests/test_js_build_version_resolution.py::test_the_typescript_project_checks_without_library_overrides
normative:
blocked_by: []
supersedes: []
---

# TypeScript project standard libraries

**Corrected in source; final receiving is recorded in the linked receipt.**
The ordinary `tsc --noEmit --project molsysviewer/js/tsconfig.json` fails with
TS2550 at `movie-import-provenance.ts:6`: `Object.hasOwn` is not part of the
implicit ES2019 library. The already used strict checks explicitly select
ES2022 and pass, which concealed the ordinary project's mismatch. Original
run `677` retains the native child exit 2 after successful lint/format.

## Resolution

Declare `ES2022`, `DOM` and `DOM.Iterable` libraries explicitly, preserving
the existing ES2019 syntax emission target. Type declarations are not runtime
polyfills or a new claim about older browsers. The public/native-host browser
baseline keeps its existing independent acceptance. The new guard invokes the
actual compiler over the real project, with no target/library override; it
protects source/configuration agreement rather than a particular JSON spelling.
#370's separate source-resolution controls remain in the same test module.

Complete duplicate review covers four pages, 369 issue/PR records and 341
issues. The [parent assessment](../molstar_integration_review_20261112.md) and
[receiving](../molstar_integration_review_receiving_20261112.json) retain the
scope, original failure, final checks and custody. No production TypeScript,
runtime bundle, installed dependency or Mol* version changes in this fix.
