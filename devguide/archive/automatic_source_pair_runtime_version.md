---
summary: Automatic source-pair validation installs a version inconsistent with the prepared runtime.
issue: uibcdf/molsysviewer#173
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: medium
verification: reproduced
area: [ci, release, export]
guard: tests/test_source_workflow_coverage.py::test_automatic_source_pair_uses_the_prepared_runtime_version
normative:
blocked_by: []
supersedes: []
---

# Automatic source-pair validation installs an inconsistent version

**Reported:** 2026-10-06, native Linux source-pair run
[37541282162](https://github.com/uibcdf/molsysviewer/actions/runs/37541282162),
Viewer `1a4c97a58b68b69f3a836546c9e4ac6187c3efa2` and MolSysMT
`46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`.

## What

The automatic Python 3.14 source-pair run returns 2,878 passed, 27 skipped,
one failed. `tests/test_exported_page_opens_from_disk.py::test_a_matching_pair_stays_quiet`
finds a real version-mismatch notice in a rendered offline export. The failure
prevents this run's later core-browser and notebook stages.

```bash
gh run view 37541282162 --repo uibcdf/molsysviewer --log-failed
```

## How

The Viewer candidate-version binding in
`.github/workflows/ci-python-314-source-pair.yaml` runs only on explicit dispatch.
Push/PR installs inherit the previous public tag's development release while
the committed runtime already identifies the next prepared version, 0.24.0.
The correct mismatch notice exposes an incoherent test pair.

Apply the existing version binding to every source event, with the intended
version as the automatic default. Validate the committed runtime before installing;
remove only the owned temporary tag afterward, preserving history and preexisting
public tags. No runtime or installed molecular library changes are needed.

## Why

The source feasibility gate must exercise a coherent Python/runtime pair and
retain full notebook/browser coverage. The installed 0.24.0 build 1 / MolSysMT
0.23.0 build 0 pair passes all sixteen native cells and the exact Windows launcher
gate. This workflow correction does not change or replace those immutable artifacts.

## What was refuted

Suppressing the notice or weakening the offline assertion would hide a real
inconsistency. Rebuilding/replacing the staged files is unnecessary: their versions
agree, all 620 installed Viewer members match the archive, and 298 affected installed
checks pass with one expected omission. Automatic-source and installed-package
qualification remain distinct. The original failing full result is preserved.

## Resolution

The version-binding step now runs for every source event. Its automatic default
and cleanup agree with the prepared version. All four workflow guards pass; the
new guard rejects event-only tagging and a fallback inconsistent with the release
plan. All eight real offline-export cases pass with the installed canonical pair,
including quiet matching versions and explicit notices for mismatches. The explicit
canonical-version source run is 37542642197 at the unchanged package candidate;
it remains running at this closure and is not counted as a full source pass.

## Correction — 2026-10-06

The subsequent automatic-source full run at `e0ae8a05` rejects the unconditional
candidate-tag approach through the existing no-retagging policy guard. The bounded
closure selection above omitted that neighboring guard and was insufficient.
`uibcdf/molsysviewer#175` restores dispatch-only canonical tagging and instead
rebuilds/reinstalls the development runtime before source validation. The exact
canonical package/source qualification at `1a4c97a5` remains unaffected and passes
on all three native hosts, with 39 Linux core suites and all 25 notebooks.
