---
summary: Exact source-pair CI omits the complete scientific notebook and browser workflows
issue: uibcdf/molsysviewer#170
status: partial
opened: 2026-10-06
closed:
severity: medium
verification: reproduced
area: [ci, documentation, interactions]
guard:
normative:
blocked_by: []
supersedes: []
---

# Exact source-pair CI omits the complete scientific notebook and browser workflows

## What

The source-pair workflow qualifies native Python but not every documented
notebook or the complete core browser product. Published-provider runs
`37519346853` and `37519346977` fail on missing `caffeine.sdf`, the experimental
Interactions API and `molsysmt.h5msm`. The separate incorrect mask example is
owned by uibcdf/molsysviewer#160.

## How

Extend the existing Linux exact-source job after the same installed-source
origin/dependency/Rust checks and full Python tests. Provision nbconvert and
ipykernel; register its actual interpreter as python3. Build runtime sources,
require hosted Chrome and execute all 39 core suites. Force every documented
notebook and retain failure logs, including when an earlier browser step fails.
Include documentation changes in the push/PR trigger.

## Why

MolSysMT needs a stable consumer commit for the coordinated package handoff.
This source coverage relates to uibcdf/molsysviewer#93, #114, #140 and #151.
It does not qualify released or staged packages. The existing published/staging
workflows and their release-gate role remain intact. Provider baseline:
`a0ceca86ec99c89377e78fac15cbdf32145a362e`.

## What was refuted

Skipping experimental tutorials or replacing the published provider silently
would make a green result misleading. The additional source observation must
remain distinct from the existing installed-artifact gates.

## Resolution

All 25 notebooks execute (82 seconds), all 39 core browser suites pass,
and strict Sphinx passes locally with the clean provider source revision.
The focused contracts pass and final archive/link checks pass 229 tests.
The once-run full Python result and resolved Git-index/link failures are
preserved in `devguide/ci_workflow_closure_20261006.json`. Hosted confirmation
of the expanded source lane is pending. Published-provider failures remain
owned by coordinated release/installed-pair work after this source fix.
