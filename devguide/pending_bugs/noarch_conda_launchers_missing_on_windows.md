---
summary: The noarch Conda package omits three MolSysViewer launchers on Windows.
issue: uibcdf/molsysviewer#101
status: partial
opened: 2026-09-24
closed:
severity: medium
verification: inspected
area: [conda, cli]
guard:
normative:
blocked_by: []
supersedes: []
---

# Noarch Conda package omits three Windows launchers

**Reported:** 2026-09-24 by the suite noarch recipe survey.
**Status:** Partial; source and verification routes exist, but no repaired
artifact has been staged or published.

## What

`pyproject.toml` declares `molsysviewer`, `molsysviewer-qt`, and
`molsysviewer-server`. The noarch Conda recipe omitted their `build.entry_points`, so
the Conda package did not create their Windows launchers.

## How

The recipe should declare the three exact script targets. An installed-package Windows
gate should install one exact staged build and verify its noarch record, channel URL
and SHA-256 before finding and executing all three commands with `--help` outside the
source checkout.

## Why

The Linux build test and source-based CI cannot establish whether Conda created
`Scripts\\<command>.exe` for Windows users. A new noarch build is needed; modifying
the recipe does not change an artifact already published under an immutable coordinate.

## What was refuted

Testing `python -m` would exercise importability rather than the installed launchers.
Running the normal source CI on Windows would not attest the staged Conda artifact.

## Acceptance criteria

- The recipe matches every `[project.scripts]` command and callable target.
- The staged Windows job verifies the exact noarch file and executes all three
  installed commands.
- A new staged build passes that hosted job before promotion or a public repair claim.
- The corresponding public build is independently verified after publication.

## Current state

The exact `entry_points` correction reached `main` through the
`policy-v1.5.2` adoption commit `c35ce1b2`; the earlier dedicated PR
`uibcdf/molsysviewer#108` was closed without a merge. The source now has
Windows jobs for exact staged and public noarch installations. They check the
installed Conda record's version, build, channel URL and SHA-256, find all three
`.exe` launchers inside the environment, and execute each with `--help` outside
the checkout. `tests/test_noarch_conda_launchers.py` checks recipe parity and
the release routes.

The public `0.23.4` tag predates the recipe correction, so its Conda file still
has the defect. Closing requires a new staged artifact, a passing hosted Windows
launcher job, promotion of that exact file, and a passing public Windows job.
Until then, the source fix is not a public repair claim.
