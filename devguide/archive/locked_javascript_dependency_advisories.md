---
summary: Locked JavaScript dependencies retain nine registry advisory findings
issue: uibcdf/molsysviewer#242
status: resolved
opened: 2026-10-13
closed: 2026-10-13
severity: high
verification: measured
area: [dependencies, frontend, tooling]
guard: tests/test_javascript_dependency_audit.py
normative:
blocked_by: []
supersedes: []
---

# JavaScript lockfile advisory review

**Reported:** uibcdf/pharmacophoremt#58 on Viewer 76c8cee1; independently
confirmed with `npm audit --json` on the current unchanged lockfile.

## What

The registry reports nine transitive findings: one critical, six high, one
moderate and one low. A compatible fix is advertised for every affected package.
This is advisory evidence, not a demonstrated exploit against MolSysViewer.

| Package | Registry severity | Inspected ownership/reachability |
| --- | --- | --- |
| proxy-addr | critical | HTTP server dependencies; no direct Viewer source import |
| body-parser | low | HTTP server dependencies; no direct Viewer source import |
| compression | high | Mol* server entry points; no direct Viewer source import |
| path-to-regexp | high | HTTP routing dependencies; no direct Viewer source import |
| qs | moderate | HTTP/query dependencies; no direct Viewer source import |
| form-data | high | Node request dependencies; zero inputs in the browser bundle probe |
| immutable | high | Mol* state tree, plugin context and snapshots use it at runtime |
| brace-expansion | high | Nested test-exclude dependency, coverage tooling |
| minimatch | high | Nested test-exclude dependency, coverage tooling |

## How

The lockfile fixes vulnerable transitive versions. Mol*'s state tree explicitly
imports Immutable Map/OrderedSet, so excluding all findings as server tooling
would be incorrect. Source inspection establishes that ownership; it does not
prove that every advisory precondition is reachable in our UI. The critical
proxy-addr advisory concerns IPv4-mapped IPv6 trust-subnet checks in HTTP servers
([GHSA-jqcg-44mw-7w3h](https://github.com/advisories/GHSA-jqcg-44mw-7w3h)).

## Why

Before freezing the next candidate, choose compatible transitive updates,
inspect their exact diff and qualify a clean locked installation, runtime build,
JS tests and browser core. Preserve the original audit and the repaired audit.
Do not infer a Mol* major upgrade is required: #115 remains post-1.0.

## What was refuted

No blind `npm audit fix`, dependency override or advisory suppression was applied.
Neither registry severity nor absence of direct imports proves canvas exposure
or absence of exposure. This review remains an actionable pre-freeze item.

## Browser bundle input review — 2026-10-13

A metadata-only esbuild probe of the configured browser entrypoint includes
Immutable (one input), and none of the other eight affected packages. It uses
`write: false` and creates no duplicate runtime output. This narrows browser
reachability; Node/coverage tools and the installed dependency graph retain
their own advisories. It does not prove the absence of all indirect or external
attack paths, nor qualify repaired bytes. Compatible transitive remediation
remains pending.

## Resolution — 2026-10-13

Compatible transitive lockfile updates repair all nine observed packages.
Immutable is 5.1.9, proxy-addr 2.0.8, compression 1.8.2, body-parser 2.3.0,
path-to-regexp 8.4.2, qs 6.16.0, form-data 4.0.6, minimatch 9.0.7 and
brace-expansion 2.1.7. Required leaf dependencies also update/deduplicate within
their parents' declared ranges. The entire Mol* 5.4.1 lock entry, root manifest
and all direct dependency entries remain identical. No force, overrides or
advisory suppression is used; #115 keeps its post-1.0 scope.

Clean npm ci and npm audit --json return zero findings at every severity.
Runtime build and the JS unit aggregate pass. The offline guard rejects the
observed advisory ranges at every lockfile depth. Core browser CI and the local
release gate now require the full live npm audit at severity low, covering later
registry notices; failure/acquisition error cannot count as a clean audit.
Browser qualification and source-suite results are retained separately in
`devguide/addon_discovery_dependency_validation_20261013.json`. Neither this
repair nor a clean audit asserts absence of all exploit paths or installed
artifact qualification.

## Correction — 2026-10-13

The resolved lockfile contains minimatch **9.0.9**. The 9.0.7 mentioned in the
resolution is the fixed lower bound, not the observed installed version. The
clean audit, compatible range and other recorded versions are unchanged.
