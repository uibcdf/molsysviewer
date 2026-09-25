---
summary: Guard the bundled Python runtime version before tagging a release
issue: uibcdf/molsysviewer#102
status: active
opened: 2026-09-25
closed:
severity: high
verification: inspected
area: [release, packaging, runtime]
guard:
normative:
blocked_by: []
supersedes: []
---

# A Python wheel can ship a runtime from an older Viewer release

**Reported:** During the coordinated MolSysMT `0.22.4` / MolSysViewer `0.23.4`
pre-tag review on 2026-09-25, the committed `viewer.js` still carried `0.23.0`.

## What

The prepared citation and Conda candidate name `0.23.4`, but the source tree's
tracked `molsysviewer/viewer.js` contains the prior `0.23.0` runtime version.
`pyproject.toml` includes this file as Python package data. A wheel built from
the tagged source without a separate JS build can therefore package an older
runtime, even while Conda and npm are correct because those routes rebuild JS.

## How

The ordinary Python build path does not run npm. The existing release gate checks
the checkout's runtime against the Python version imported from the current
environment; before a tag this may be a versioningit development version from an
unrelated editable install. It does not inspect a built wheel. The candidate
staging workflow instead runs `npm run build` in a private Conda source copy,
so its successful noarch package does not prove the general Python wheel route.

## Why

Python package data is a public distribution surface. A version mismatch can
produce exported views that load a runtime built against another protocol or
option schema. This is a pre-release integrity blocker even when the coordinated
Conda installed-pair matrix and npm publication path pass.

## What was refuted

The passing Conda staging build is not sufficient evidence for wheels built
directly from a Git tag: its private build script regenerates the asset first.
The npm publisher also regenerates it, but that affects only the npm artifact.

## Resolution

The candidate source runtime was regenerated from `RELEASE_VERSION=0.23.4`
with the ignored development `_version.py` temporarily absent. The new
`devtools/validate_python_wheel_runtime.py` rejects a source bundle whose
compiled runtime version differs from the intended release, and a wheel whose
METADATA and packaged runtime disagree. `tests/test_validate_python_wheel_runtime.py`
proves the old-version and wrong-metadata cases fail, a matching wheel passes,
and an uninspectable bundle fails closed. The staged/direct Conda build workflow
now creates and validates an ordinary Python wheel *before* its separate Conda
build rebuilds JS. The release guide specifies the clean-checkout build order.
The staging-enabled Viewer CI now creates the same local tag at its exact
workflow SHA before installing Python, so its browser export tests compare
the release runtime with a matching package version. An untagged local suite
run had 2,120 passes, 14 skips, and one expected version-mismatch failure in
`test_a_matching_pair_stays_quiet`; that specific test passed when the
generated local package version was set to the intended `0.23.4`. The other
2,120 results are retained as diagnostic source evidence, not a green full
release suite. JavaScript unit tests pass 292/292.
The first hosted wheel preflight (`36119181642`) failed before any Conda upload:
`python -m build --no-isolation` reported that `wheel` was absent from the
build environment. The source-version check had passed. `wheel` is now an
explicit member of `devtools/conda-envs/build_env.yaml`; build number 4 was
not published by that failed run and can be retried without overwriting a
staged artifact.
The source-pair run `36119181575` then passed macOS and Windows but failed
the Ubuntu exported-page matching-version test for the same reason as the
untagged local checkout: it installed the Viewer candidate without a release
tag while testing a `0.23.4` runtime. Its manual dispatch now validates the
source bundle and creates the intended tag at the exact Viewer workflow SHA
before installing either source candidate. This makes the 3.14 source-pair
gate test the release identity, not a development-version approximation.
The corrected build-4 workflow `36120275908` passed the actual wheel
METADATA/runtime comparison and produced the noarch staging package. It is
diagnostic for the final candidate because the source-pair workflow correction
was committed afterward; that next candidate needs a new build number.

The local focused guard passes five tests. This report remains active until the
new workflow succeeds on the corrected exact candidate and the release wheel
contract is observed, then the issue can close with that test module as guard.
