---
summary: Locked body-parser retains compressed-request denial-of-service advisory.
issue: uibcdf/molsysviewer#266
status: partial
opened: 2026-10-26
closed:
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
`/tmp/msv-body-parser-audit.json`. Hosted Core E2E 40389716226 is in progress.
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
