---
summary: Extend MolSysViewer Python support to 3.14 alongside MolSysMT.
issue: uibcdf/molsysviewer#93
status: active
opened: 2026-09-22
closed:
verification: measured
area: [packaging, ci, deps]
guard:
normative:
blocked_by: []
supersedes: []
---

# Extend MolSysViewer Python support to 3.14 alongside MolSysMT

**Reported:** 2026-09-22 during the MolSysSuite Python 3.14 transition
(`uibcdf/molsyssuite#29`). This is paired with `uibcdf/molsysmt#237`.
**Status:** Active feasibility work; no public Python 3.14 support is claimed.

## What

Extend the tested Python interval to 3.11–3.14 for the core MolSysViewer
package and its noarch Conda artifact, coordinated with MolSysMT's extension
and hard dependency. Preserve the existing 0.22.0 MolSysMT / 0.23.1
MolSysViewer staging campaign for 3.11–3.13 under
`uibcdf/molsysmt#195` and `uibcdf/molsysviewer#82`.

## How

1. Build and test the two source distributions in one isolated Python 3.14
   environment without treating bypassed current package metadata as a support
   claim. Check the viewer's bundled runtime resources and its real MolSysMT
   integration path.
2. Resolve code or dependency incompatibilities found by focused tests, then
   run the full Python suite. Include Linux and macOS Python 3.14 in the
   required CI matrix, retaining 3.11–3.13. Keep the recommended development
   interpreter on 3.13 unless the suite changes that policy.
3. After the pair passes, update `requires-python`, classifiers, noarch host
   and run constraints, distribution tests, and package documentation together.
   Do not edit the already-inspected staging artifact or reuse its coordinate.
4. Build a later exact staged pair and test clean installation of both packages
   across the claimed Python and platform matrix. Public release and central
   admission require independent package-channel verification.

## Why

MolSysMT requires MolSysViewer at runtime, while MolSysViewer requires
`molsysmt>=0.22.0`. Its staged 0.23.1 noarch package currently declares
`python>=3.11,<3.14`. A Conda dry run of `python=3.14
molsysviewer=0.23.1` with staging, uibcdf, and conda-forge failed on that
bound. MolSysMT's Linux Python 3.14 wheel feasibility under
`uibcdf/molsysmt#237` cannot become a supported paired installation until
MolSysViewer participates.

## What was refuted

- `noarch: python` does not itself imply support for future interpreters. One
  artifact serves the range in its metadata; its source and dependencies must
  be tested on 3.14 before widening that range.
- Changing only MolSysMT's metadata cannot solve a package pair whose viewer
  half explicitly excludes 3.14.

## Current evidence and open gates

- Source `pyproject.toml`, Conda recipe, and the Linux/macOS CI matrix currently
  stop at Python 3.13. `tests/test_distribution_artifact.py` intentionally
  guards their agreement. The routine development and documentation jobs use
  Python 3.13 and need not move merely to add a supported minor.
- The core Python package is pure Python plus a bundled JavaScript runtime.
  The optional Qt host has a separate native dependency stack; investigate
  its Python 3.14 availability explicitly rather than silently making core
  support depend on it or claiming Qt support without evidence.
- Full source tests, installed-pair tests, cross-platform Conda resolution,
  and a new immutable release remain open. The existing 0.23.1 staging
  artifact is evidence only for its declared 3.11–3.13 interval.
- A local Linux/Python 3.14.7 pair probe built the unmodified source wheels
  from MolSysMT `fe0be24b8` and MolSysViewer `251f7759`. Both installed with
  `--no-deps --ignore-requires-python`; the installed MolSysMT Rust extension
  passed 99 exports, BCIF conversion produced 596 atoms, and a real
  `MolSysView(debug_js=True)` loaded that native system. MolSysViewer's
  MolSysMT/runtime integration selection passed 19 tests with 12 workers.
  The bypassed metadata and missing release version make this feasibility
  evidence, not a clean supported installation.
- In the isolated `python-3.14-support` worktree, candidate metadata
  `>=3.11,<3.15` built and installed without bypassing the Python bound;
  the packaged-runtime wheel test passed. `pip check` still reports that
  MolSysViewer requires `molsysmt>=0.22.0` while this MolSysMT source tree
  identifies itself as development version `0.21.0+...`. An exact later
  candidate is required before resolver-consistent pair evidence exists.
- A separate Conda dry run for `python=3.14 pyside6-addons-uibcdf=6.9.2`
  failed: its `shiboken6-uibcdf` dependency requires `python_abi=3.13`.
  This optional Qt host must not be claimed on 3.14 without a compatible
  package and its own Qt tests. It does not invalidate the core notebook
  viewer probe above.
- The candidate branch adds a two-platform Python 3.14 source-pair workflow
  with MolSysMT pinned to exact commit
  `3485f8ddf0924f307dd8a089dea4ed8b51276600`. It exercises the full
  Viewer Python suite against locally built sources without ignoring Python
  metadata. It deliberately omits `pip check`: the source checkout's 0.21.x
  development identity is below Viewer's release floor and is not an exact
  staged pair. This workflow is a source-compatibility gate, not a release
  or package-admission gate.
- A local 12-worker full Viewer suite run on Python 3.14 collected 2,090
  tests: 2,069 passed, five failed, and 16 skipped. Four failures were
  environmental (`jinja2` and `mdtraj` omitted from the initial probe
  environment); both resolve on Linux/Python 3.14 and are now in the source
  workflow environment. The fifth was a pre-existing stale generated
  capability audit: its generator finds three first-release tags at 0.8.0
  where the checked-in document said 0.9.0. The document was regenerated.
  The three affected test files then passed 208 tests. This is not a clean
  full-suite run; the hosted two-platform workflow remains the required
  confirmation.

## Resolution

Pending.
