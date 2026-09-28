---
summary: Evaluate the latest conda-forge PySide6/Qt for a future supported standalone host.
issue: uibcdf/molsysviewer#113
status: open
opened: 2026-09-28
closed:
verification: inspected
area: [standalone, packaging, release, testing]
guard:
normative:
blocked_by: []
supersedes: [uibcdf/molsysviewer#112]
---

# Evaluate the latest conda-forge PySide6/Qt for a supported standalone host

**Reported:** 2026-09-27, after the Linux Python 3.14 development environment
migrated to official PySide6/Qt 6.11.2.
**Status:** Opened 2026-09-28 after the release-scope decision. This is a
post-1.0 experimental-host evaluation, not a condition for the core 1.0
candidate. It supersedes the earlier pre-1.0 timing in
`uibcdf/molsysviewer#112`.

## What

Before claiming a supported standalone host, check the newest aligned
PySide6/Qt family available from conda-forge and dogfood the optional Linux host
against it. The likely next version is 6.11.3, but the actual candidate must
be discovered then; a later version may be available, or some modules may lag.
Choose the version on evidence, not recency alone.

## How

Record exact conda-forge builds and channels for `pyside6`, `qt6-main`,
`qt6-webengine`, and `qt6-positioning`; verify that the family solves
coherently for the supported Python range. Create a clean environment and
run the Viewer standalone and WebEngine transport tests, representative
MolSysMT–Viewer workflows, an Xvfb/software-render smoke, and the separate
visible-window human-workflow observations required for host certification.
Compare with the validated 6.11.2 baseline. Record regressions and the
release decision, including exact artifact coordinates. A successful solver
or Xvfb smoke alone is not visible-window certification.

If the newest available family passes, advance the host candidate pins and
repeat its exact-candidate checks. If it does not, retain 6.11.2 for the
experimental host with a documented reason and a bounded follow-up. Keep the
UIBCDF fork family as a separate rollback lane until `uibcdf/molsyssuite#57` reaches its
retirement decision; never mix namespaces in the canonical environment.

## Why

The central Python 3.14 development environment and the Viewer host now use
official conda-forge 6.11.2 successfully. That proves a usable current route,
not that the same patch version should be frozen for future host support. A
host-support candidate is the right moment to compare the latest available
family under real dogfooding while changes can still be evaluated without silently
altering a published release.

## What was refuted

Automatically upgrading whenever conda-forge publishes a newer patch would
change native dependencies without exact-candidate evidence. Conversely,
pinning 6.11.2 through host certification without revisiting it could miss
fixes relevant to Qt WebEngine or PySide6. A solver-only pass cannot stand in for the real
host or visible-window observations.

## Scope and acceptance

This is the Viewer-local standalone selection and dogfooding decision. The
existing canonical migration is `uibcdf/molsysviewer#109`, and the
supported-platform boundary is `uibcdf/molsysviewer#97`. Suite-wide fork
retirement remains under `uibcdf/molsyssuite#57`. Linux development
evidence does not grant native macOS/Windows standalone support.

Close when the supported-host candidate record names the accepted aligned
version, exact conda-forge builds and channels, representative dogfooding and
Qt-host test evidence, remaining platform limits, and the rationale for
either advancing or deliberately retaining 6.11.2. The core 1.0 tag may
precede this decision because the host remains experimental in 1.0.
