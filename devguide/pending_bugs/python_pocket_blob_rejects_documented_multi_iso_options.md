---
summary: Python pocket blob API rejects its documented multi-iso options.
issue: uibcdf/molsysviewer#99
status: active
opened: 2026-09-24
closed:
severity: medium
verification: reproduced
area: [shapes, documentation, testing]
guard:
normative:
blocked_by: []
supersedes: []
---

# Python pocket blob API rejects documented multi-iso options

**Reported:** 2026-09-24, when staged-dependency Documentation notebooks run
`35997846329` reached executable content and failed in the pocket Showcase.

## What

`view.shapes.add_pocket_blob(iso_levels=[0.08, 0.15],
iso_colors=[0x44CCFF, 0x003366], iso_alphas=[0.35, 0.5], ...)` raises
`UnknownArgumentError` naming `iso_levels`. The same hosted run also failed
`channels.ipynb` because it uses a removed `smoothing` spelling; that separate
documentation correction belongs to `uibcdf/molsysviewer#88`.

## How

`molsysviewer/shapes/pocket_blobs.py` declares only the scalar `iso_level` in
its public Python signature, so ArgDigest rejects the plural arguments before
the message is constructed. The frontend already declares all three plural
options in `PocketBlobOptions` and renders one surface per level. Python
digesters for the three arguments also exist. The missing part is the Python
signature, serialization, and a contract guard for matching per-iso lengths.

## Why

The Showcase advertises a capability that a Python caller cannot reach, and
the resulting exception prevents hosted notebook execution from becoming a
real 1.0 gate. A source-only test that uses just `iso_level` cannot detect it.

## What was refuted

This is not a missing frontend implementation: `preparePocketBlobData` already
iterates `options.iso_levels`. It is also not a Conda solver failure: the
staging-based workflow installed successfully and reached the failing cell.
Silently replacing the example with one scalar surface would hide the
existing multi-iso contract rather than connect it.

## Resolution in progress

The Python pocket-blob and generic scalar-isosurface APIs now accept the three
plural options and reject empty levels, conflicting scalar/plural levels, and
per-level arrays of the wrong length. Focused tests cover both the serialized
message and the real public `MolSysView.shapes` path. `channels.ipynb` now calls
`smoothing_subdivisions`, and both affected notebooks execute locally.

The first full local suite reached 2,098 passes, 14 accepted skips, and one
generated devguide-index failure caused by adding this report. The index was
regenerated; the focused source/API/distribution/reporting slice then passed
135 tests with 12 workers, and Ruff passed. Hosted Documentation notebooks
run `36016496850` passed on exact branch commit
`7c4e0cd968e9530033e35221683ca085fe1d37cd`, including every documented
notebook. The defect remains open until the fix reaches the release branch or
`main`; success on this source branch is not public-channel admission.
