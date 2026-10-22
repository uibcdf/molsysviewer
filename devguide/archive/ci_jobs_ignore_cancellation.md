---
summary: Core CI jobs keep running after ordinary workflow cancellation
issue: uibcdf/molsysviewer#256
status: resolved
opened: 2026-10-21
closed: 2026-10-22
severity: medium
verification: reproduced
area: [ci, workflows]
guard: tests/test_ci_backlog.py::test_test_jobs_stop_on_cancellation_without_losing_recovery_routes
normative:
blocked_by: []
supersedes: []
---

# Core CI jobs survive ordinary workflow cancellation

**Reported:** 2026-10-21 while completing accepted source d126c5a1 CI.

## What

Normal cancellation acknowledges the superseded palette-trial runs, but four
CI/CI_e2e campaigns keep running test jobs. Native inspection finds ongoing
core E2E and macOS Python tests after the requests; other tests even finish
successfully in the interval. Source-pair and experimental Qt campaigns accept
the same ordinary cancellation operation.

Affected runs: 39667006466, 39667006383, 39666318075 and 39666318197.
The accepted d126c5a1 campaign is excluded from every cancellation selection.

## How

`CI.yaml:jobs.test.if` and `CI_e2e.yaml:jobs.e2e.if` start with `always()` and
have no explicit cancellation exclusion. GitHub re-evaluates job conditions
during cancellation; its [cancellation reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-cancellation)
documents that an `always()` job can continue. The intended skipped-backlog
handling has unintentionally made test jobs resistant to cancellation.

## Why

Superseded source campaigns consume runner capacity while accepted-source
qualification waits. This is an operator/control defect, not evidence of a
notebook renderer or scientific-model regression.

## Operational recovery and remaining work

After preserving before/after job snapshots and verifying exact identities,
request force cancellation only for still-active superseded runs. GitHub
[documents this recovery](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows)
when ordinary cancellation does not process. Never treat a cancelled run as a
passing result; do not select package, tag, promotion or installed-pair campaigns.

The pipeline correction remains open: add cancellation-aware test-job gating
while retaining push/PR/dispatch and nightly-backlog semantics, then guard those
conditions. Current source receiving can complete independently through the
operational recovery. No runtime or qualification assertions are weakened.

Raw snapshots and cancellation receipts are retained under
`/tmp/msv-final-source-ci-20261021/`, including `superseded-cancellations.json`.

Recovery completed: 39667006383 and 39666318197 required force cancellation;
both now have the native terminal conclusion `cancelled`. The two older E2E
runs became cancelled before a force request was needed. All eight selected
superseded campaigns are cancelled; none supplies passing qualification.
The final d126c5a1 campaigns remain untouched. This operator recovery does not
resolve the workflow-condition defect.

## Correction in progress — 2026-10-22

Main CI, core E2E and experimental Qt test-job conditions now use the explicit
status function `!cancelled()` in place of `always()`. This still overrides the
implicit success check for skipped/failed nightly dependencies and preserves
ordinary push/PR/dispatch and fail-open nightly recovery. The PR result gate
also stops on workflow cancellation; temporary-tag cleanup steps retain
`always()` because cleanup has a different owner and purpose.

The guard evaluates the actual bounded test-job expressions for push, PR,
dispatch, skip marker, explicit backlog probe, nightly debt/no-debt and decision
failure, with each case both cancelled and non-cancelled. It is not a GitHub
scheduler emulation. Hosted ordinary-cancellation receiving is recorded
separately; cancelled probes cannot qualify scientific/browser results.

## Resolution — 2026-10-22

Resolved in `e4f8c7c5`. Test jobs and the PR result gate now use
`!cancelled()`; Qt diagnostic steps stop on cancellation while retaining
execution after an earlier test failure. Short temporary-tag cleanup and result
preservation retain their distinct `always()` ownership.

The selected guard evaluates all three actual job expressions across eight
push/PR/dispatch/backlog/recovery scenarios, each cancelled and non-cancelled
(48 cases). The remaining backlog module and core/Qt guards pass as well.
Hosted ordinary-cancellation runs 39709607361, 39709610393 and 39709613748
observed all eight matrix jobs, core E2E and Qt actively running, then all
cancelled after one ordinary request per workflow. No force cancellation was
used. These intentional cancellations are not passing scientific/Qt results.
Three control-only backlog probes and exact-source policy pass; the once-run
local core passes 3,224 tests, with 21 skips and 12 Qt deselections.
See [receiving](../pre_documentation_cleanup_20261022.json) for native identities,
before/after summaries, hashes and retained source-qualification limits.
