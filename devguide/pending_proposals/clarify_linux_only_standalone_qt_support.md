---
summary: Clarify the Linux-only support boundary of the Qt standalone host.
issue: uibcdf/molsysviewer#97
status: open
opened: 2026-09-24
closed:
verification: inspected
area: [documentation, packaging, standalone]
guard:
normative:
blocked_by: []
supersedes: []
---

# Clarify the Linux-only support boundary of the Qt standalone host

**Reported:** 2026-09-24 during the coordinated MolSysMT/MolSysViewer
Python 3.14 and Windows source-pair work, after a maintainer asked how
Windows core support relates to the UIBCDF Qt/PySide packages.

## What

Audit and align all support claims for MolSysViewer's optional Qt standalone
host. At present, the validated UIBCDF Qt/PySide recipe is Linux-specific,
whereas the core MolSysViewer package is a separate `noarch: python`
distribution with a Windows source-pair test lane. A user should be able to
see the distinction before attempting `molsysviewer-qt` on Windows or macOS.

This proposal does **not** promise that the core Windows lane already passes;
`uibcdf/molsysviewer#93` owns that evidence.

## How

1. Verify the exact public-channel subdirectories, versions, and coordinates
   of the five UIBCDF Qt/PySide packages, separately from the local 6.10.1
   candidates. Record the date and source of that inventory.
2. State a small platform/capability matrix consistently in the README,
   installation guide, standalone user documentation, and
   `devguide/standalone_supported_environment.md`: core notebook/browser
   viewer; Qt desktop host; published packages; and validated candidate
   builds. Keep `noarch` from being read as a Qt-host platform promise.
3. Explain the supported non-Qt route on Windows/macOS and the explicit
   behavior when `PySide6_uibcdf` is unavailable. Do not silently substitute
   canonical `PySide6`; the host imports `PySide6_uibcdf`.
4. Add a check that detects contradictory or unqualified platform-support
   claims on the maintained surfaces. Revisit the matrix as other-platform
   packages earn their own gates.

## Why

The current `devguide/standalone_supported_environment.md` calls its
Conda-native recipe supported without first naming Linux, while its direct
file-install example uses `conda-bld/linux-64`. The README describes the
Jupyter viewer but does not set out a standalone platform boundary. The
Python 3.14 source-pair work now tests the core on Windows, so it is easy to
infer incorrectly that the separate native Qt host is available there.

The candidate 6.10.1 Qt family has been built and exercised locally on
Linux, including a real MolSysViewer Qt integration test. That evidence must
not be transcribed into a published Windows/macOS support claim.

## What was refuted

- A `noarch: python` MolSysViewer artifact does not carry or validate the
  native Qt/PySide family on each platform.
- Canonical `PySide6` is not an automatic drop-in for the current host, which
  imports the UIBCDF namespace.
- The existing Linux package-path examples are not an adequate warning to
  readers who see an earlier unqualified "supported" recipe.

## Scope and acceptance

This is a documentation/support-contract issue. Building Qt packages for
Windows or macOS, choosing future release coordinates, and changing the
optional dependency graph are outside scope. It can close when a reader can
find one consistent, versioned statement of the supported platform matrix
from the README and installation guide, with links to the detailed Qt recipe,
and an addressable guard protects the distinction from regression.

## Resolution

Pending.
