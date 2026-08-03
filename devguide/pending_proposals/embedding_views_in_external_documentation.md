# Embedding views in external documentation

**Status:** approved. The governing decision, the proposed names and the fate of
the CDN path are all confirmed (2026-08-03). Ready to execute in the order of
§5.

**Origin:** MolSysMT collaborators are blocked on publishing views in their
documentation. Investigating why produced
[`../pending_bugs/docs_lite_views_pinned_to_unpublished_npm_version.md`](../pending_bugs/docs_lite_views_pinned_to_unpublished_npm_version.md)
and the documentation findings in
[`first_read_comprehension_gaps_2026_08.md`](first_read_comprehension_gaps_2026_08.md).
This proposal is the design that closes both.

**Audience:** a third party publishing MolSysViewer views on their own website.
Not a MolSysViewer developer. That distinction is the reason this work exists —
today every description of the mechanism lives in the developer guide.

---

## 1. The governing decision

> **Reproducibility over freshness.** An exported view must keep rendering what
> it rendered when it was published, offline, without depending on a third-party
> CDN, on our npm release cadence, or on a future runtime version.

This is not a preference between two good options. `guiding_principles.md` §1
makes exportable, replayable state the centre of the product. An artifact that
stops working when a registry entry disappears — or that silently renders
differently a year later — is not that.

The tension is real and was weighed. A floating CDN pin would deliver bug fixes
to already-published views without the author regenerating them. It was rejected
because:

- the runtime has repeatedly changed visible behaviour (layered colour, Contract
  S9 framing, whole-representation succession), so a newer runtime over an older
  scene is not a safe assumption;
- `engineering_rules.md` §2 declares breaking changes rather than softening them
  and refuses shims, which is precisely the compatibility promise a floating pin
  assumes;
- the author cannot test what their readers will see;
- and the benefit only reaches authors who **never rebuild** — the population
  least able to notice when it breaks.

The freshness the objection asks for is real and is preserved: an author who
upgrades MolSysViewer and rebuilds their site gets the new runtime, because the
asset is copied from the installed package. They get it deterministically, under
their control, and having seen it before publishing.

## 2. Current state, measured 2026-08-03

- `mode="lite"` writes one runtime candidate: a jsDelivr URL pinned to the
  exporting installation's version (`core.py:3435-3436`).
- npm `@uibcdf/molsysviewer` stops at `0.7.0`; Python is at `0.20.0`. **Every
  export produced today is dead on arrival**, including every export from a git
  checkout.
- `_build_lite_html` already accepts `runtime_urls: Sequence[str] | None` and
  the generated HTML resolves each candidate with
  `new URL(rel, window.location.href)` and falls through on failure. **Relative
  local paths already work.** The mechanism exists; `exports.py::html()` does not
  expose it.
- `viewer.js` ships in the wheel and conda package
  (`pyproject.toml` `package-data`), so every user already has a version-exact
  runtime on disk.
- On total failure the page writes a visible message and a console error. The
  browser-side diagnostic is adequate; the build-side check does not exist.
- MolSysViewer's own docs work only because `docs/conf.py` rewrites the pinned
  version at build time — a hook third parties do not have. **We do not run the
  path we document.**

## 3. Decisions

1. **`mode="lite"` sources the runtime from a local asset by default.** Behaviour
   change, declared per `engineering_rules.md` §2. No shim.
2. **`mode`'s own default stays `"standalone"`.** It is the right default for
   "one self-contained file to send someone". Only what `lite` *means* changes.
   This keeps the change to one behaviour, not two.
3. **Three public entry points, with distinct jobs**: the export parameter for
   the common case, a standalone asset accessor for build systems, and the
   explicit candidate list as an escape hatch.
4. **The asset copy is idempotent by version, not by existence.** A shared asset
   with N views introduces a skew the CDN did not have — regenerate one view
   after upgrading and scene and runtime diverge. Overwriting on version
   mismatch is what keeps the shared asset honest.
5. **The exported HTML declares the runtime version it expects, and the runtime
   checks it**, reporting visibly through the same channel that already reports
   a failed load. Mismatch must not be silent.
6. **CDN remains a supported path, opt-in, pinned exact** — confirmed, for
   authors who do not want to host a runtime at all. Support costs two things,
   and both are part of the decision:

   - **Publishing to npm becomes a standing release gate**, not a packaging
     chore (`path_to_1_0.md` task 7). Every release, or that release's users get
     dead views. Thirteen unpublished versions is how the present defect
     happened.
   - **The export refuses to write a URL it can predict is dead.** A version
     that is not a publishable release — any development or local version, which
     is what every git checkout produces — raises at export time naming the
     problem. No network call: inspecting the exporting version is free and
     catches the common case. A remote check belongs to the build, not to the
     export.

   Note that the case usually given for the CDN — *not wanting a 6.4 MB blob in
   my repository* — has a better answer than the CDN. The asset can be generated
   at build time and gitignored: any CI that builds the views already has
   MolSysViewer installed, so copying the runtime is one more line in the same
   script. That leaves the CDN for the genuinely narrow case: a standalone page
   with no build step, or deliberate cache sharing across separate sites.
7. **The `conf.py` rewrite hook is removed** and our own docs move to the
   documented path. What we tell third parties must be what we run.

## 4. Proposed surface

Names confirmed 2026-08-03.

```python
view.export.html(
    "docs/_static/views/1tcd.html",
    mode="lite",
    runtime="local",                    # "local" (default) | "cdn" | [urls...]
    runtime_assets_dir="docs/_static",  # where the shared runtime lives
)
```

- `runtime="local"` — ensure `viewer.js` is present in `runtime_assets_dir` at
  the installed version, and write a **relative** URL from the HTML to it. The
  relative path is computed by the code, never by the user: today's cookbook
  spends three paragraphs explaining `../../../_static/views/`, and a wrong path
  fails only when a reader opens the page.
- `runtime="cdn"` — today's behaviour, pinned exact.
- `runtime=[...]` — explicit candidates, tried in order. This is the existing
  `runtime_urls`, promoted to public. It also expresses "local first, CDN as
  backup" for anyone who wants both.

Plus, for build systems that want the asset without constructing a scene:

```python
molsysviewer.tools.export_runtime_asset("docs/_static") -> Path
```

`molsysviewer.tools.*` is already declared public in `public_api.md`.

**Validation:** `runtime` is meaningless when `mode="standalone"`, where the
runtime is inlined. Passing both must raise, not be ignored.

**No CLI for now.** `engineering_rules.md` §1 orders public Python method first,
and the existing console scripts (`molsysviewer`, `molsysviewer-qt`) are flat
argparse launchers with no subcommands — adding one means restructuring a public
entry point. `python -m` over the public function covers the build-system case
until someone asks for more.

## 5. Execution order

1. **The Python primitive** — the export parameter, the asset accessor, version
   coherence, tests with mutations.
2. **The runtime handshake (TypeScript)** — declared version, checked and
   reported. `npm run build:runtime` last, per `engineering_rules.md` §3.
3. **Dogfood** — move our own docs to the documented path, delete the `conf.py`
   rewrite hook and the vestigial `require.js` / `nglview-js-widgets`
   registrations, regenerate the committed views. **The pending bug closes
   here**, as a consequence rather than as a separate patch.
4. **One user-facing page** — "Embedding views in your website", in the *user*
   guide, framework-agnostic first (the output is an HTML file plus one asset,
   which works in Sphinx, MkDocs, Quarto, Jupyter Book, Hugo, plain HTML and
   paper supplementary material). Every existing description links to it and
   stops describing the mechanism itself.
5. **Port to MolSysMT** — never before step 3. Porting a mechanism we do not yet
   run ourselves is how the current misunderstanding propagated.
6. **A Sphinx extension** — deferred until a real user asks. With `runtime`
   exposed and the asset accessor available, what remains for it is per-page
   relative-path computation and build-time failure. That is convenience, not
   safety: the browser already reports a failed load.

## 6. Acceptance

- **Headline:** a view exported from an ordinary git checkout renders when
  opened. Today it does not, and that is the defect this proposal exists to
  remove.
- The exported page loads with the network disabled.
- Mutation: make the asset copy skip when any `viewer.js` already exists,
  regardless of version. The version-coherence test must go red. If it stays
  green, prove the mutated path executed before judging the test —
  `engineering_rules.md` §5.
- Mutation: point the asset resolution at a missing directory. The export must
  fail loudly rather than write a dead relative URL.
- The runtime reports a scene/runtime version mismatch visibly, verified by
  pairing a scene with a deliberately mismatched runtime.
- MolSysViewer's own documentation builds with no rewrite hook in `conf.py`, and
  every file under `docs/_static/views/` loads from the committed tree without a
  build step.
- `mode="standalone"` plus `runtime=` raises.
- `runtime="cdn"` from a development or local version raises at export time,
  naming the version. Mutation: remove that check and the test must go red —
  today the export writes the dead URL without complaint, which is the whole
  defect.
- Generating the asset at build time into a gitignored directory produces a
  working site, so the documentation can present it as the alternative to
  committing the runtime.

## 7. Out of scope

- Floating CDN pins. Reconsider only if 1.0 commits to semver for the scene
  format, which the current no-shims policy does not.
- Changing `mode`'s default.
- The Sphinx extension (step 6, deferred).
- Whether the copied asset is committed or generated at build time. That is the
  adopting project's repository policy, and the documentation should present
  both without prescribing.
