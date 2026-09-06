# Docs lite views are rewritten to an npm version that was never published

**RESOLVED 2026-08-04.** Kept for the evidence, which is still the clearest
account of how a green build produced a dead site.

The pinned-CDN mechanism this describes no longer exists. A shared runtime is
copied from the installed package and addressed relatively
(`_private/runtime_asset.py`), the `conf.py` rewrite hook is gone, and
`tests/test_docs_static_views.py` fails if any committed view reaches the
network. The CDN survives only as an opt-in (`shared_runtime="cdn"`, which
refuses to write a URL from an unpublishable version) and as a last-resort tail
candidate on released exports, which is reached only when a page is opened from
a disk. Recommendation 2 stands and is unfinished: publishing to npm is a release
gate, `path_to_1_0.md` task 7.

---

**Status:** confirmed against the deployed site and the public registries on
2026-08-03. Not yet visible to users, because the published site is frozen at
the last version that reached npm. It breaks on the next docs deploy.

**Affected contract:** the documentation embedding path — `view.export.html(...,
mode="lite")` plus `docs/conf.py::_update_docs_light_runtime_links`. This is the
mechanism `docs/content/developer/docs.md`, `dev_setup.md`, `concepts.md`,
`documentation/web/editorial_guidelines.md` and the
`sphinx_html_embedding.ipynb` cookbook all tell users to adopt.

## Symptom

A `mode="lite"` export loads the runtime from jsDelivr and carries the scene as
inline JSON. `_update_docs_light_runtime_links`, hooked to `builder-inited`,
rewrites the pinned CDN version in every `docs/_static/views/*.html` to
`molsysviewer.__version__` on each build.

It does not check that the resulting URL resolves. The npm package is thirteen
versions behind the Python package, so the rewrite currently targets a tarball
that does not exist.

## Evidence

Measured 2026-08-03.

Published site — https://www.uibcdf.org/molsysviewer/ reports version `0.7.0`,
and its views request:

```
https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@0.7.0/dist/viewer.js
```

npm registry, `@uibcdf/molsysviewer`:

```
versions:    0.0.2, 0.5.3, 0.6.0, 0.6.1, 0.7.0
dist-tags:   latest = 0.7.0
```

jsDelivr resolution:

| Version | Where it appears | HTTP |
|---|---|---:|
| `0.7.0` | the deployed site | **200** |
| `0.14.0` | the HTML committed under `docs/_static/views/` | **404** |
| `0.20.0` | what the next build will write (`molsysviewer.__version__`) | **404** |

Reproduce:

```bash
curl -s https://www.uibcdf.org/molsysviewer/_static/views/demo_dialanine.html \
  | grep -o 'https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@[^"]*'
curl -s https://registry.npmjs.org/@uibcdf%2Fmolsysviewer | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['dist-tags'])"
for v in 0.7.0 0.14.0 0.20.0; do
  curl -s -o /dev/null -w "$v %{http_code}\n" \
    "https://cdn.jsdelivr.net/npm/@uibcdf/molsysviewer@$v/dist/viewer.js"
done
```

## Why it has not been noticed

Two reasons, and both matter for the fix.

1. **The deployed site is frozen at `0.7.0`.** It works because it has not been
   rebuilt since the last version that was published to npm. The mechanism is
   sound; the publication step it depends on stopped happening.
2. **The failure is silent at build time only.** Sphinx stays green, the pages
   generate, the iframes load. No build step, test or link check looks at the
   CDN — the failure `engineering_rules.md` §4 calls *the silent skip*.

   *(Corrected 2026-08-03: an earlier revision of this report claimed the
   failure was silent in the browser too. It is not. The generated HTML ends
   its candidate loop with `console.error("[MolSysViewer docs] Failed to load
   runtime.", lastError)` and writes `"MolSysViewer failed to load. See console
   for details."` into the mount element, so quality target #6 is satisfied on
   the runtime side. The reader sees a message, not an empty frame. The gap is
   entirely in the build.)*

The committed HTML under `docs/_static/views/` is already in the broken state:
pinned at `0.14.0`, which jsDelivr 404s. A local build rewrote it and the result
was committed. Anyone opening those files outside a fresh build gets no viewer.

## The defect is wider than the deploy

The pinned version comes from the exporting installation:

```python
base_version = _pkg_version.split("+", 1)[0]      # core.py:3435
```

Measured in this checkout, `molsysviewer.__version__` is
`0.20.0+96.g6362914c.dirty`, which pins to `0.20.0` — not on npm. **Any export
produced from a git checkout is dead on arrival**, and so is any export from a
release whose npm publish did not happen. A `mode="lite"` export is only valid
when the exporter happens to be running exactly a version that reached the
registry, which since `0.7.0` is none of them.

Note also that `+...dirty` is stripped, so a scene produced by modified code
declares a released runtime version. That is a provenance problem independent of
whether the URL resolves.

## Cause

Three independent gaps compose into one defect:

1. **`_update_docs_light_runtime_links` rewrites blind.** It substitutes the
   current version without verifying that it resolves, so a correct build
   produces a broken site.
2. **The npm publish is not part of the release.** `path_to_1_0.md` task 7
   ("Publish conda + npm packages") has carried no status since `0.18.0`. It
   reads as packaging housekeeping; it is in fact what serves the runtime for
   every interactive view on the documentation site.
3. **The build rewrites versioned source in place.** Writing into
   `docs/_static/views/` during `builder-inited` means the committed artifacts
   drift to whatever version last built locally, which is how `0.14.0` was
   committed.

## Recommended correction

1. **Fail the build instead of writing a dead link.** Before substituting, issue
   a `HEAD` against the target URL; on anything other than success, raise and
   stop the build with the attempted version in the message. A documentation
   build that cannot produce working views must not succeed quietly.
2. **Make the npm publish a release gate**, recorded in `path_to_1_0.md` task 7,
   and state the coupling explicitly where the embedding mechanism is
   documented: the docs site's 3D depends on `@uibcdf/molsysviewer@<version>`
   existing on npm.
3. **Regenerate and commit the lite views against a published version**, so the
   files in the tree are openable as they stand.
4. Consider whether the rewrite should target the current version at all. Two
   safer policies exist: pin to the newest *published* version, or treat the
   version baked in at export time as authoritative and only verify it. Decide
   deliberately rather than by default.

Unrelated but adjacent: `docs/conf.py::setup` still registers `require.js` and
`nglview-js-widgets@3.1.0` from CDN. MolSysViewer's own views use neither — it
is inherited from the MolSysMT configuration and can go.

## Acceptance

- With the current version absent from npm, `make html` **fails**, naming the
  version it could not resolve. Today it succeeds and ships dead links.
- Mutation: point the rewrite at a version known to be absent and confirm the
  build turns red. If it stays green the guard is not wired — per
  `engineering_rules.md` §5, prove the guarded path executed before concluding
  anything about it.
- Every file under `docs/_static/views/` requests a version that resolves,
  checked from the committed tree rather than from a fresh build.
- The release checklist contains the npm publish, and closing it is recorded
  with the published version.

## Scope note

The same embedding mechanism is what MolSysMT's `docs/README.md` declares and
does not implement; see
[`../pending_proposals/first_read_comprehension_gaps_2026_08.md`](first_read_comprehension_gaps_2026_08.md)
for the documentation-accuracy pattern. Fix this defect before porting the
mechanism to another repository, or the port inherits it.
