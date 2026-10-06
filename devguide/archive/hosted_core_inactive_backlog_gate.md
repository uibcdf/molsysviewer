---
summary: Hosted core evidence rejects the expected inactive backlog decision job.
issue: uibcdf/molsysviewer#174
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [ci, release]
guard: tests/test_release_evidence.py::test_hosted_core_allows_only_inactive_backlog_control
normative:
blocked_by: []
supersedes: []
---

# Hosted core evidence rejects an inactive control job

**Reported:** 2026-10-06, exact-candidate verification of Viewer 0.24.0 build 1,
commit `1a4c97a58b68b69f3a836546c9e4ac6187c3efa2`.

## What

Hosted core run [37541292806](https://github.com/uibcdf/molsysviewer/actions/runs/37541292806)
succeeds with all 39 real-browser suites. Independent `release_gate.py --pre-release
--only conda,hosted_e2e,public_conda` passes the sixteen staging environment inventories,
blocks the absent public run, but incorrectly fails hosted core with
`required job did not complete successfully`.

## How

`devtools/release_evidence.py::check_jobs` requires every job to succeed.
`CI_e2e.yaml` also defines the conditional `Check skipped-commit backlog` job,
which runs only for a schedule/probe. An ordinary core dispatch legitimately
reports this control job as completed/skipped. The checker mistakes that control
state for omitted scientific validation.

Allow that exact inactive control job only in the hosted profile, after validating
inventory completeness, run/attempt ownership, completion and lack of duplicates.
Keep all required core steps and every scientific matrix cell strict. Failed
control jobs and unknown skipped jobs must still fail.

## Why

The gate must reflect complete core validation while retaining its refusal of
missing scientific evidence. The fix belongs to developer tooling; it changes
no Viewer package, runtime, candidate or installed environment.

## What was refuted

Broadly accepting skipped jobs would let omitted scientific checks pass. Removing
the backlog job from CI would discard an independently useful control. The existing
39-suite hosted run already supplies the required product observation; rerunning
it cannot fix its interpretation by the checker. No public-channel result exists,
and the public gate must remain blocked.

## Resolution

All 66 evidence checks pass. The nine-case guard accepts the expected inactive
control and still rejects failed controls, unknown skips, omitted core jobs/steps,
duplicate controls, foreign attempts and incomplete inventories. The corrected
reader independently verifies staging and hosted core for the fixed 1a4c97a candidate.
All sixteen downloaded environment archives and their digests are retained under
`/tmp/msv-024-build1-exact-evidence-20261006`. The public gate remains BLOCKED
with no exact run; no release clearance or publication is claimed.
