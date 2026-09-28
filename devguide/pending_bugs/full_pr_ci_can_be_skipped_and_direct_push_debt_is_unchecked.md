---
summary: Full PR CI can be skipped and direct-push CI debt is unchecked.
issue: uibcdf/molsysviewer#116
status: active
opened: 2026-09-28
closed:
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
- The first actual nightly schedule and an external PR check remain distinct
  hosted evidence; neither is claimed from a manual probe or a direct push.

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

## Resolution

Open until the hosted implementation, required checks and review evidence
are recorded. The first actual nightly event and first external PR remain
follow-up evidence if they cannot occur during this implementation window.
