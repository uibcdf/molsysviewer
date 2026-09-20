---
summary: Conda package embeds dirty MolSysViewer version metadata
issue: uibcdf/molsysviewer#91
status: active
opened: 2026-09-20
closed:
severity: high
verification: reproduced
area: [packaging, release]
guard:
normative:
blocked_by: []
supersedes: []
---

# Conda package embeds dirty MolSysViewer version metadata

**Reported:** 2026-09-20, in the exact MolSysMT--MolSysViewer staging matrix.
**Status:** active; the package is rejected by the coordinated gate and a corrective
non-overwriting build is being prepared.

## What

The staged coordinate `molsysviewer-0.23.1-py_0` installs Python distribution metadata
and `molsysviewer.__version__` as `0.23.1+0.g736e8274.dirty` rather than `0.23.1`.
MolSysMT run `35499866604` rejects the mismatch in every matrix cell whose environment
solves.

## How

`devtools/conda-build/build.sh` regenerates `molsysviewer/viewer.js` and updates JS
metadata before `pip install`. Those tracked build products make the checkout dirty, so
the later PEP 517 invocation asks `versioningit` for a dirty local version even though
Conda has already fixed `PKG_VERSION` from the ephemeral candidate tag.

The corrective build freezes `PKG_VERSION` into the ephemeral `pyproject.toml` and
`molsysviewer/_version.py`, and removes versioningit's build hook from that private copy,
before generating JS assets. The source repository retains dynamic VCS versioning; only
conda-build's private source copy is frozen.

## Why

An immutable Conda coordinate and its installed Python metadata must name the same
release. Accepting the local-version suffix would hide a non-reproducible package
identity and make provenance checks dependent on which API reports the version. The
defect blocks the coordinated MolSysMT 0.22.0/MolSysViewer 0.23.1 release gate.

## What is measured and what is assumed

**Measured:** run `35499866604` observed `0.23.1+0.g736e8274.dirty` on Linux x86_64,
both macOS platforms, and all Python 3.11--3.13 cells that reached validation.

**Measured:** the Conda channel record itself is version `0.23.1`, build `py_0`; the
mismatch is inside the installed distribution, not the solver coordinate.

**Measured locally:** setting only static project metadata was insufficient: the
versioningit command hook still rewrote `_version.py` as dirty. Removing that hook from
the ephemeral copy produced both exact wheel metadata and an exact runtime version file.
The resulting dirty-source wheel was named `molsysviewer-0.23.1-py3-none-any.whl`, its
METADATA reported `Version: 0.23.1`, and its packaged `_version.py` reported `0.23.1`.

**Assumed pending hosted confirmation:** the complete correction will produce an exact
internal `0.23.1` in corrective build 1.

## What was refuted

The failing check is not source-checkout shadowing: `importlib.metadata` reads the
installed distribution record. It is not a MolSysMT version problem; that package's
record and internal `__version__` pass first in the same validator.

## Scope and exclusions

This covers exact version identity in the Conda package and monotonic build numbers. It
does not publish a GitHub Release, move a tag, promote a package to the main channel, or
change MolSysViewer's public API.

## Acceptance criteria

- A unit test requires version freezing before generated assets modify the source tree.
- The Conda recipe test requires both distribution metadata and `__version__` to equal
  `PKG_VERSION` exactly.
- Corrective build 1 is additive and passes the exact installed-pair gate; build 0 is not
  overwritten.
- The eventual public release uses a distinct build number.

## Dependencies and risks

The exact-pair matrix also found missing MolSysSuite support packages on Linux ARM and
Windows. That independent solver gap can keep cells from reaching this version check,
but it does not weaken or replace the exact identity requirement.

## Provenance

GitHub Actions run `35499866604`, MolSysMT 0.22.0 build 3, MolSysViewer 0.23.1 build 0,
Python 3.11--3.13, Linux x86_64, macOS Intel and macOS ARM, 2026-09-20. Evidence captured
with GH Run Receptor's Conda profile and checked against the cached authoritative logs.
