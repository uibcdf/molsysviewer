---
summary: Adopt the shared Python and Ruff development baseline.
issue: uibcdf/molsysviewer#87
status: active
opened: 2026-09-12
closed:
verification: measured
area: [process, ci]
guard:
normative:
blocked_by: []
supersedes: []
---

# Adopt the MolSysSuite Python tooling policy

## What

Align MolSysViewer with the Python-library contract governed by
`uibcdf/molsyssuite#6`: declare Python `>=3.11,<3.14`, use Python 3.13 for
development, and enforce Ruff as formatter, import sorter, and linter.

## How

Tighten the existing Python upper bound, pin the suite-tested Ruff release in the
development environment, remove Black from active developer guidance and dependencies,
and invoke the reusable MolSysSuite conformance workflow. Preserve the repository's
broader Ruff/Bugbear rules and Python/TypeScript test surfaces.

## Why

MolSysViewer is one of the six wave-1 libraries being stabilized first. Explicitly
bounding the supported Python minors and sharing the same quality gate makes coordinated
changes with MolSysMT and the foundational libraries cheaper and more predictable.

## Evidence

The policy 1.0 checker on 2026-09-12 reported `PYTHON_RANGE` and a missing Ruff format
CI gate. The local Ruff configuration already covers the shared baseline and excludes
the synchronized guides. Inspection also found Black in the development environment and
contributor instructions, although the central checker does not currently inspect that
environment file.

## Acceptance criteria

- The central conformance checker reports no findings.
- Ruff lint and format checks pass with the suite-tested release.
- The relevant MolSysViewer Python tests pass.
- The local issue and this record close together after the guard is published.

