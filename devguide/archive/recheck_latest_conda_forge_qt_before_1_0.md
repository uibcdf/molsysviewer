---
summary: Evaluate the latest conda-forge PySide6/Qt in standalone dogfooding before 1.0.
issue: uibcdf/molsysviewer#112
status: superseded
opened: 2026-09-27
closed: 2026-09-28
verification: inspected
area: [standalone, packaging, release, testing]
guard:
normative:
blocked_by: []
supersedes: []
---

# Evaluate the latest conda-forge PySide6/Qt in standalone dogfooding before 1.0

**Reported:** 2026-09-27, after the Linux Python 3.14 development environment
migrated to official PySide6/Qt 6.11.2.
**Status:** Open; this is a pre-1.0 release-preparation decision, not a request
to change the current working environment immediately.

## What

At the 1.0 candidate freeze, check the newest aligned PySide6/Qt family
available from conda-forge and dogfood the optional Linux standalone host
against it. The likely next version is 6.11.3, but the actual candidate must
be discovered then; a later version may be available, or some modules may lag.
Choose the version on evidence, not recency alone.

## How

Record exact conda-forge builds and channels for `pyside6`, `qt6-main`,
`qt6-webengine`, and `qt6-positioning`; verify that the family solves
coherently for the supported Python range. Create a clean environment and
run the Viewer standalone and WebEngine transport tests, representative
MolSysMT–Viewer workflows, an Xvfb/software-render smoke, and the separate
visible-window human-workflow observations required by the 1.0 gate.
Compare with the validated 6.11.2 baseline. Record regressions and the
release decision, including exact artifact coordinates. A successful solver
or Xvfb smoke alone is not visible-window certification.

If the newest available family passes, advance the candidate pins and
repeat the exact-candidate gates. If it does not, retain 6.11.2 for 1.0 with
a documented reason and a bounded follow-up. Keep the UIBCDF fork family
as a separate rollback lane until `uibcdf/molsyssuite#57` reaches its
retirement decision; never mix namespaces in the canonical environment.

## Why

The central Python 3.14 development environment and the Viewer host now use
official conda-forge 6.11.2 successfully. That proves a usable current route,
not that the same patch version should be frozen for 1.0. The release
candidate is the right moment to compare the latest available family under
real dogfooding while changes can still be evaluated without silently
altering a published release.

## What was refuted

Automatically upgrading whenever conda-forge publishes a newer patch would
change native dependencies without exact-candidate evidence. Conversely,
pinning 6.11.2 through 1.0 without revisiting it could miss fixes relevant
to Qt WebEngine or PySide6. A solver-only pass cannot stand in for the real
host or visible-window observations.

## Scope and acceptance

This is the Viewer-local pre-1.0 selection and dogfooding decision. The
existing canonical migration is `uibcdf/molsysviewer#109`, and the
supported-platform boundary is `uibcdf/molsysviewer#97`. Suite-wide fork
retirement remains under `uibcdf/molsyssuite#57`. Linux development
evidence does not grant native macOS/Windows standalone support.

Close when the 1.0 candidate record names the accepted aligned version,
the exact conda-forge builds and channels, representative dogfooding and
Qt-host test evidence, remaining platform limits, and the rationale for
either advancing or deliberately retaining 6.11.2. The 1.0 tag must not
precede this decision.

## Superseded — 2026-09-28

The release-scope decision made the local standalone launchers and Qt host
experimental for 1.0. Their certification no longer blocks the core 1.0 tag.
This report preserves the earlier timing decision as history. The same Qt
version comparison, now attached to a future supported-host candidate, is
tracked in `uibcdf/molsysviewer#113` and the active post-1.0 proposal.
