---
summary: The noarch Conda package omits three MolSysViewer launchers on Windows.
issue: uibcdf/molsysviewer#101
status: active
opened: 2026-09-24
closed:
severity: medium
verification: inspected
area: [conda, cli]
guard: tests/test_noarch_conda_launchers.py::test_noarch_recipe_declares_every_project_script
normative:
blocked_by: []
supersedes: []
---

# Noarch Conda package omits three Windows launchers

**Reported:** 2026-09-24 by the suite noarch recipe survey.
**Status:** Active; source repair is prepared, installed-artifact evidence is pending.

## What

`pyproject.toml` declares `molsysviewer`, `molsysviewer-qt`, and
`molsysviewer-server`. The noarch Conda recipe omitted their `build.entry_points`, so
the Conda package did not create their Windows launchers.

## How

The recipe declares the three exact script targets. A manual Windows workflow installs
one exact staged build and verifies its noarch record, channel URL and SHA-256 before
finding and executing all three installed commands with `--help` outside the source
checkout.

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

Source recipe, Windows workflow, and local guards are prepared. No hosted staged
artifact run or public repair claim has been made yet.
