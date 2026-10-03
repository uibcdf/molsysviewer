---
summary: Full PR CI can be skipped and direct-push CI debt is unchecked.
issue: uibcdf/molsysviewer#116
status: resolved
opened: 2026-09-28
closed: 2026-10-01
severity: high
verification: measured
area: [ci, governance]
guard: tests/test_ci_backlog.py
normative:
blocked_by: []
supersedes: []
---

# Full PR CI can be skipped and direct-push CI debt is unchecked

**Reported:** 2026-09-28, while reviewing the MolSysSuite Python CI contract
in `uibcdf/molsyssuite#39` against MolSysViewer's current workflows and branch
settings. The source and hosted baseline were `6f49013c8` and scheduled run
`36455949357`.

## What

The Monday CI run passed the complete Python matrix on Linux and macOS for
Python 3.11–3.13, plus the Qt pipeline. That success does not enforce the same
suite on external PRs. `CI.yaml` ignores documentation/YAML-only PRs, and its
test and Qt jobs can be skipped by a PR title or branch. `CI_e2e.yaml` has the
same PR skip conditions. GitHub returned `Branch not protected` for `main`,
and the repository had no rulesets, so no full-suite check was required before
integration. The only current collaborators, Diego (`dprada`) and Liliana
(`LMMV`), have administrator access and need to retain direct pushes.

Deliberate `[skip ci]` on a direct push can suppress CI without any daily
recovery of the omitted full suite. That route is useful for rapid internal
development, but repeated skipped commits can accumulate without a fresh
test signal.

## How

Keep the existing direct-push route and its current push test selection. For
every PR, run the six Python jobs, JavaScript unit step, Qt pipeline and core
browser E2E, regardless of file paths, title or branch name. Publish a stable
`PR full suite` aggregate for the Python/JS/Qt workflow and a stable `Core E2E`
job. Require both checks on `main`, with administrator enforcement disabled so
the two internal developers can still push directly.

The Monday full matrix remains unconditional. At 00:17
`America/Mexico_City`, the main CI workflow checks for skipped commits since
its last successful *executed* complete run and starts its full matrix and Qt
pipeline only while they remain due. At 00:27, the E2E workflow makes the same
decision against its own successful core E2E watermark. A failed or missed
run does not clear either backlog; an API or history error runs the lane.
Manual `probe_backlog=true` checks either decision without launching tests and
cannot count as a successful full run.

## Why

The suite policy permits deliberately skipped direct pushes for named
maintainers only when a conditional daily full recovery protects the backlog.
External changes must use a PR whose complete suite is required before
integration. The existing weekly green run is useful evidence, but workflow
conditions and branch settings presently leave those contributor routes
unenforced.

## What was refuted

The successful scheduled matrix alone does not prove PR protection: schedule
does not exercise PR title/branch filters, path filters or branch settings.
Requiring only the Python matrix would also miss the separate core browser
E2E workflow. A diagnostic probe is not a full-suite watermark because its
heavy jobs are intentionally skipped.

## Acceptance and evidence

- `tests/test_ci_backlog.py` exercises skip detection, complete-run
  watermarks, conservative fallback and workflow wiring.
- The hosted direct-push CI, E2E and policy gates pass at the implementation
  commit. A manual backlog probe exercises each detector on GitHub.
- The branch protection API requires `PR full suite` and `Core E2E`, while
  direct administrator pushes remain available.
- The actual 2026-10-01 nightly CI and core E2E schedules executed their
  required test steps successfully. The first external contributor PR remains
  an observation to collect; it is not inferred from an administrator PR.

The local focused tests for this guard, the existing staging-workflow
contract, and the reporting protocol pass; Ruff also passes. One local full
`tests/` run failed beyond this CI change. The staging-workflow assertion was
fixed by preserving the existing order of manual inputs. Representative
remaining failures show that the isolated local environment lacks the JS
`esbuild` package and cannot bind loopback ports for server tests. The hosted
matrix installs JS dependencies and provides the authoritative result for
this implementation commit.

The first hosted probes (`36476458223` and `36476470801`) exposed a detector
query mistake: the API request combining `branch=main` with `status=success`
returned no runs, although the same workflow endpoint without that status
filter returned the green scheduled run. The detector now reads branch runs
and checks each run's `conclusion` plus the required executed job steps itself.
The probes were diagnostic, so they did not launch a duplicate heavy suite.

## Resolution — 2026-10-01

Resolved. The implementation at `500c556297748457f968f2ea0391e82d8645affd`
passed [CI 36476235643](https://github.com/uibcdf/molsysviewer/actions/runs/36476235643),
[core E2E 36476235487](https://github.com/uibcdf/molsysviewer/actions/runs/36476235487)
and [policy 36476236673](https://github.com/uibcdf/molsysviewer/actions/runs/36476236673).
Native job steps confirm six executed Python matrix cells, the Ubuntu 3.13 JS
unit step, both Qt pipeline observations, and the core browser test step.
A skipped decision or PR-only aggregate on a push is not a missing test lane.

Corrected detector probes at `ad4357176720a18f1937fe6ef504e8a08339b3e6`
([CI 36477025996](https://github.com/uibcdf/molsysviewer/actions/runs/36477025996),
[E2E 36477036433](https://github.com/uibcdf/molsysviewer/actions/runs/36477036433))
found one skipped commit due in each independently anchored lane. They did not
execute the heavy suites and are not full-run watermarks.

The actual 2026-10-01 schedules at
`1a7f20e66a5f2aeef1979c5c96f23e70fb241830` passed
[CI 36868653948](https://github.com/uibcdf/molsysviewer/actions/runs/36868653948)
and [E2E 36869441160](https://github.com/uibcdf/molsysviewer/actions/runs/36869441160).
Native steps show the matrix, JS, Qt and core E2E tests really ran. The current
branch-protection API requires `PR full suite` and `Core E2E`, with strict checks
and administrator enforcement disabled; force pushes and deletion remain disabled.

The four tests in `tests/test_ci_backlog.py` pass locally on 2026-10-01.
Their assertions protect skip detection, executed-lane watermarks, conservative
API failure behavior, unfiltered PR triggers, required aggregate dependencies,
and nightly/probe wiring. GH Run Receptor 1.1.1 was used for first inspection;
native GitHub job records verified the executed steps and branch settings.
The implementation and actual nightly/protection evidence close this defect.
The first external contributor PR is still an observation to collect, not a
remaining implementation dependency or a claim made from these runs.

## Additional PR evidence — 2026-10-01

Administrator draft PR #135 at `4ef65a8e5403ace672e571bd0123aab7becfae71`
passes CI `36885559251` and core E2E `36885559507`. Native steps confirm
all six Python cells, JS, both Qt pipeline observations, the successful
`PR full suite` aggregate and executed `Core E2E`. This is actual PR-event
evidence in addition to the previously recorded push and nightly results;
it is not an external contributor/fork observation or real-window standalone
certification.
