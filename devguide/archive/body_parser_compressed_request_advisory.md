---
summary: Locked body-parser retains compressed-request denial-of-service advisory.
issue: uibcdf/molsysviewer#266
status: resolved
opened: 2026-10-26
closed: 2026-10-26
severity: high
verification: reproduced
area: [dependencies, frontend, tooling]
guard: tests/test_javascript_dependency_audit.py
normative:
blocked_by: []
supersedes: []
---

# Locked body-parser retains compressed-request denial-of-service advisory

**Reported:** 2026-10-26, authorized by the principal maintainer after PBC addon receiving.

## What

`npm audit --audit-level=low` stops Core E2E 40388498107 on aacf4252
before browser execution: locked body-parser 2.3.0 has one high finding under
[GHSA-27r3-jxmh-p828](https://github.com/advisories/GHSA-27r3-jxmh-p828).
The advisory concerns process termination from trailing bytes after compressed
request bodies; no exploit against the Viewer canvas was exercised.

## How

The locked graph includes Mol* -> Express -> body-parser. The observed 2.x
range is fixed by body-parser 2.4.0. Its qs dependency requires 6.16.1.
The existing live audit correctly blocks new registry findings; the old
known-range offline guard still allowed body-parser 2.3.0.

## Why

The next candidate needs a clean locked graph. This is a new advisory,
separate from the earlier set closed in uibcdf/molsysviewer#242. Leaving
mandatory audit enforcement intact prevents a false green browser lane.

## What was refuted

The failure is not an E2E behavioral result, an addon/PBC calculation failure
or proof that the canvas exercises the vulnerable HTTP path. A Mol* upgrade,
overrides and audit suppression are unnecessary: two compatible transitive
updates suffice.

## What is measured

Fix 5246d409 updates only body-parser and qs package entries. npm ci succeeds;
the replacement lockfile's live audit returns zero findings at every severity;
all 332 JS unit cases pass. The original failing log is
`/tmp/msv-pbc-host-close-e2e.log`, and the correction's raw audit is
`/tmp/msv-body-parser-audit.json`. That initial checkpoint preceded terminal browser receiving recorded below.
The original PBC provider CI 9061e2149 retains its separate successful scope.

## Acceptance criteria

Extend the offline known-range guard, preserve the mandatory live audit, and
verify the corrected locked installation and real core-browser lane before
closing. Retain source/CI/log provenance and distinguish source receiving
from installed-artifact qualification.

## Resolution

Source repair 5246d409 is delivered. The offline guard now rejects the observed
2.x range through <2.4.0 at every lockfile depth. Its two focused cases pass;
the combined guard/reporting/link check passes 286 cases. Original corrected-lock
Core E2E 40389716226 and the broader source lanes remain in progress/queued.
Qt experimental 40389716287 fails its transport/WebGL observations and is not
counted as passing core evidence. Closure awaits the hosted browser result;
installed-artifact qualification is outside this report.

## Terminal receiving — 2026-10-26

Exact guard head 4be459a40fb8df0d4613c68b6bb1ae61fb3d7714 passes Core E2E
40391698362: all 44 real Mol*/Chrome suites complete, with the mandatory npm
audit passing before harness/browser execution. Local clean installation,
zero findings, 332 JS unit cases and 286 combined guard/reporting/link cases
retain their earlier evidence. The behavioral guard is
`tests/test_javascript_dependency_audit.py`: it rejects the observed vulnerable
2.x range at every lock depth and requires live audit before browser execution.
Fix 5246d409 and guard 4be459a4 therefore satisfy this advisory's acceptance.

The original terminal browser log `/tmp/msv-4be459a4-core-e2e.log` has SHA-256
`46b80b77dc242e2e047255926588eef6e5f624b1e2e16033bf7b5b2424cd49c6`.
This does not make global CI green: 40391698358 has six failing Python cells
and 40391697507 has three failing source-pair cells, each with the same three
warning-strict documentation failures under historical MolSysMT 0.23.0 and
newer pandas. They retain the separate known uibcdf/molsysmt#431 receiving gap;
its source repair 128a0bbb9 is not a qualified corrected public package here.
Qt experimental also retains its separate failures. None is suppressed or
relabeled as passing. Source advisory closure is not installed qualification.
