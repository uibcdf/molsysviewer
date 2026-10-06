---
summary: Exact source-pair CI omits the complete scientific notebook and browser workflows
issue: uibcdf/molsysviewer#170
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [ci, documentation, interactions]
guard: tests/test_source_workflow_coverage.py::test_exact_source_pair_executes_all_notebooks_and_core_browser_suites
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

The exact-source workflow on
`d7939f08d604138112edfe84ccc9bc4a40428057` now includes the complete consumer
workflows. Run `37523291585` passes all three native platforms. Its Linux job
executes **39/39 core browser suites**, including 17 real calculation forms and
10 geometry fixtures, followed by **25/25 documented notebooks** (59 seconds).
No browser skip or experimental-tutorial exclusion is used. The guard rejects
loss of the documentation trigger, full runners, correct kernel/browser and
failure-log path. The source origin, dependency and native-resource checks
precede these observations. Local 25-notebook, 39-browser, strict Sphinx and
contract results are retained in `devguide/ci_workflow_closure_20261006.json`.

Normal published/staging workflows and their release-gate role are unchanged.
The published provider still lacks required capabilities; compatible installed
artifacts remain pending under #93/#114/#140/#151. The corrected #160 get
notebook now also passes against that published provider. Qt's hosted WebGL
failure is the already recorded experimental-host finding under #109.
