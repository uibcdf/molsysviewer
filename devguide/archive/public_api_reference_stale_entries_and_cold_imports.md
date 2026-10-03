---
summary: Remove stale API reference entries and cold-import failures in the docs build.
issue: uibcdf/molsysviewer#117
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: low
verification: reproduced
area: [docs, api]
guard: tests/test_public_reference_imports.py
normative:
blocked_by: []
supersedes: []
---

# Stale public reference entries and cold imports

**Reported:** 2026-09-30 while verifying the Interactions tutorial under
`uibcdf/molsysviewer#114`. This is separate reference cleanup; the new tutorial
executes successfully and its concept page builds.

## What

`make -C docs html` exits successfully but emits seven warnings. The authored
`docs/api/public/api_public.rst` still advertises `MolSysView.get` and
`MolSysView.select`, which do not exist. Their generated pages are outside the
toctree. Autosummary also reports a cold import failure for `molsysviewer.shapes`:
`ImportError: cannot import name 'Annotation' from partially initialized module
'molsysviewer.layers' (most likely due to a circular import)`.

## How

Correct the authored reference to match the public query/selection managers,
and remove the import-order dependency. Investigate the leaf-module path through
`layers -> viewer.utils -> viewer.core -> annotations -> layers`. Regenerate
reference files through the documentation tooling. Do not manually patch generated
pages or suppress these warnings as the correction.

## Why

A successful Sphinx exit cannot certify that the public reference is usable or
matches the API. A future resolution needs fresh-process module-import evidence
and reference validation that rejects retired API entries. This report records
the observed build without claiming those guards or a fix already exist.


## Implemented correction (2026-09-30)

`viewer/__init__.py` now materializes `MolSysView` only when requested, matching
its top-level package entrypoint. Importing leaf utilities no longer initializes
`viewer.core`, so Layers, Shapes and Interactions import from a cold process.
The public class remains available through both existing import paths and is
cached after materialization. No scientific algorithm or scene behavior changed.

The authored public reference no longer advertises retired facade `get/select`
methods and now includes the native interaction manager and set. Regenerated
reference files came from `docs/clean_api.py` and Sphinx, without manual edits.
A full reference regeneration also exposed the stale Annotations page link in
`representations/types.md`; it now points to the existing labels guide.

`tests/test_public_reference_imports.py` checks three cold scene imports,
materializes the real public class through both paths, resolves every authored
public-reference entry in a fresh process and validates the representation
page's actual document targets. Together with the existing lazy-root test,
**six focused tests passed**. Reintroducing the eager package import, retired
reference entry and removed Annotations page each made its relevant test fail.
Original file bytes were restored in finally blocks after each mutation.

`make -C docs html SPHINXOPTS=-W` passed with no warnings. Ruff and whitespace
checks passed. The required full Python regression for this entrypoint fix passed once in
the canonical Python 3.14/Qt 6.11.2 environment: **2,235 passed, 20 skipped,
no failures** (240.88 s). The guard module protects the actual fresh-process
cycle and resolves the authored API/document targets, rather than checking
only their spelling. The result does not qualify omitted real-window/GPU
scenarios or the experimental interaction provider release.
