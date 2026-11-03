---
summary: Exclude new glob and minimatch advisory ranges from coverage tooling.
issue: uibcdf/molsysviewer#289
status: resolved
opened: 2026-11-02
closed: 2026-11-02
verification: reproduced
severity: medium
area: [dependencies, ci, testing]
guard: tests/test_javascript_dependency_audit.py
normative: devguide/dependency_contract.md
blocked_by: []
supersedes: []
---

# Coverage dependency advisories

The current lockfile at Viewer `481319a9` produces four affected package
entries from two new moderate advisories: glob GHSA-3g3m-2fjr-6pw4 and
minimatch GHSA-g3hv-75wg-m249. Their c8/test-exclude ancestors are also reported.
The live audit fails before browser qualification. This is public registry
evidence, not an observed exploit in the Viewer. #242/#266 remain historical.

## Resolution — 2026-11-02

Keep c8 10.1.3 and Mol* 5.4.1 unchanged. Two overrides scoped to test-exclude
resolve glob 14.0.3 and minimatch 11.0.4. The complete production lock graph is
byte-for-byte equal as decoded lock entries; changes and removals are confined
to development dependencies. The development environment now requires Node 22,
consistent with the existing test/source-pair lanes and these tool engines.
No runtime bundle or TypeScript production source is changed.

Clean npm ci and the complete live audit pass with zero advisories. The original
334 JS cases pass before and after under native Node 22; an additional real
filesystem test receives glob sync/async traversal, include/exclude rules,
negation and extension filtering through the actual installed test-exclude.
All 335 final JS cases pass, with no omissions. The offline known-range guard
now protects both advisories at every lockfile depth. Seven directed Python
policy/diagnostic checks and the separate 68-case route selection pass.

This is a bounded tooling compatibility override, not an upstream claim that
test-exclude 7 declares these major ranges. Viewer maintainers own it under
#289. Remove it when a maintained c8/test-exclude release directly declares
unaffected glob/minimatch versions, rechecking actual include/exclude traversal,
JS tests, engines and the complete live audit. Reassess before the next candidate
freeze. No dependency downgrade, Mol* upgrade, audit omission or scientific
assertion change is used.

The c8 command also exposes a pre-existing empty LCOV: zero bytes and no source
records before and after the correction. This does not invalidate the observed
335 real test passes, but supplies no numerical source coverage. Independent
#290 owns its correction; no coverage result is manufactured or claimed here.
Restricted-sandbox runs that only report the file container are diagnostic
controls, not complete test-case receiving. Native Node 22 logs retain actual
case counts. Original audit/lock hashes and all scopes are retained in the
2026-11-02 source receipt. Hosted CI retains its separate identity and status.
