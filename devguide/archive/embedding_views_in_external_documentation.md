# Embedding views in external documentation

**COMPLETE 2026-08-05.** Every step of §5 is closed.

Steps 1, 3 and 4 landed on 2026-08-03; §8 records the export rework that followed.
Step 2 was deferred to
[`exported_page_self_declaration.md`](exported_page_self_declaration.md),
which is still open and whose trigger has now arrived. **Step 5 — port to
MolSysMT — was done by MolSysMT**, from this specification, without us touching
their repository: see the adoption report and our reply, archived beside this
file. Step 6, the Sphinx extension, remains deferred until a real user asks, as
designed.

The mechanism it describes is now documented for users in *Embedding a view in
your website*, which is where a third party should read it. This file is the
record of why it is shaped the way it is.

**Status:** executed except for §5.5 (port to MolSysMT) and §5.6 (Sphinx
extension, deferred). Steps 1, 3 and 4 landed 2026-08-03; the export rework of
2026-08-04 is recorded in §8 and changed what "self-contained" means.

**Origin:** MolSysMT collaborators are blocked on publishing views in their
documentation. Investigating why produced
[`../archive/docs_lite_views_pinned_to_unpublished_npm_version.md`](../archive/docs_lite_views_pinned_to_unpublished_npm_version.md)
and the documentation findings in
[`first_read_comprehension_gaps_2026_08.md`](../pending_proposals/first_read_comprehension_gaps_2026_08.md).
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

1. **A shared runtime comes from the installed package, not from a registry.**
   Behaviour change, declared per `engineering_rules.md` §2. No shim.
2. **The self-contained file stays the default.** It is the right default for
   "one file to send someone"; sharing is what you ask for.
3. **One argument expresses the choice**, plus two `tools` helpers — an asset
   accessor for build systems and an iframe builder that computes the path. See
   §4; the first implementation had three arguments and was simplified before
   any external adopter.
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

## 4. Public surface

Simplified 2026-08-03, before the first external adopter. The first
implementation exposed `mode`, `runtime` and `runtime_assets_dir` — three
arguments for what is one question. Collapsed into one:

```python
view.export.html(path)                                  # self-contained
view.export.html(path, shared_runtime="docs/_static")   # shared with your other views
view.export.html(path, shared_runtime="cdn")            # hosted by the registry
view.export.html(path, shared_runtime=[url, url])       # explicit candidates
```

`mode` is **gone** from the export surface: sharing a runtime is what a lite
export *is*, so it is derived rather than asked for. A docs author no longer has
to learn an internal distinction of ours to answer a question that was never
about modes. `"cdn"` is the one reserved string; a directory of that name is
written `"./cdn"`.

Two helpers in `molsysviewer.tools`, already public per `public_api.md`:

```python
msv.tools.export_runtime_asset("docs/_static")      # place the asset alone
msv.tools.embed_iframe(view, path=page)             # the <iframe>, path computed
msv.tools.preview("docs/_build/html")               # serve it, so a browser will render it
```

*(`preview` added 2026-08-04; see §8. Also `python -m molsysviewer.preview
docs/_build/html`, which is the form a docs author actually types.)*

`embed_iframe` exists because counting `../` by hand is the one step of embedding
that fails silently — the export succeeds, the build succeeds, and the reader
gets an empty frame.

**No CLI for now.** `engineering_rules.md` §1 orders public Python method first,
and the existing console scripts (`molsysviewer`, `molsysviewer-qt`) are flat
argparse launchers with no subcommands — adding one means restructuring a public
entry point. `python -m` over the public function covers the build-system case
until someone asks for more.

*(The simplification was done before writing to the MolSysMT team, deliberately:
`engineering_rules.md` §2 allows breaking changes because there are no external
users, and that is true today and stops being true the moment they adopt. A
tighter surface costs an afternoon now and two repositories later.)*

## 5. Execution order

1. **The Python primitive** — the export parameter, the asset accessor, version
   coherence, tests with mutations.
2. ~~**The runtime handshake (TypeScript)**~~ — **deferred 2026-08-03** to
   [`exported_page_self_declaration.md`](exported_page_self_declaration.md),
   together with a second item raised in the same conversation: an exported page
   offers controls it cannot honour without an authority. Neither blocks
   MolSysMT, and both guard failures that are not active yet. That file records
   what ends the deferral for each.
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
  every file under `docs/_static/views/` addresses the runtime that the build
  places, by a relative path, with no network URL anywhere.

  *(Amended during execution, 2026-08-03. This criterion first read "loads from
  the committed tree without a build step", which would have required committing
  a second 6.1 MB copy of `viewer.js` beside the one already tracked at
  `molsysviewer/viewer.js` — doubling the blob churn of every runtime rebuild for
  a repository whose documentation is meant to be built. Our own asset is
  therefore generated at build time and gitignored, and `tests/test_docs_static_views.py`
  checks the declared target rather than a placed file. For third parties both
  policies remain presented without prescribing one; see §7.)*
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

## 8. Amendment, 2026-08-04: what "self-contained" was hiding

Executing §5.3 exposed a question this proposal never asked: **can the reader
open the file?**

Measured on real exports:

- a **shared** view cannot be opened from a disk at all. A page with no origin
  may not import the runtime beside it — see
  [`classic_script_runtime_for_offline_bundles.md`](../pending_proposals/classic_script_runtime_for_offline_bundles.md)
  for the browser evidence. On a served site the question never arises, which is
  why it went unnoticed;
- the **self-contained** export, meanwhile, fetched `require.js` from cdnjs and
  two `@jupyter-widgets` bundles from jsDelivr at open time. It opened from a
  disk, but only with a network. Six and a half megabytes that did not render on
  a plane.

So the default that this proposal chose for "one file to send someone" (§3.2) was
right about the shape and wrong about the file.

**Decided and done.** Both shapes are now built by `_build_lite_html`. A
self-contained export embeds the runtime in the page and boots it from a blob the
page makes itself — a blob belongs to the page, so it survives an opaque origin —
and reaches no third-party host at all. The ipywidgets template, the three CDN
dependencies and the second export path are gone.

Three consequences worth carrying forward:

1. **The recommendation in §3.2 is now defensible.** Self-contained means: opens
   with a double click, no server, no network. Shared means: for a served site.
   The user page states both as a table rather than implying both work
   everywhere.
2. **`tests/test_exported_page_opens_from_disk.py`** opens the exported file in a
   real browser, because no amount of reading the file can tell you whether a
   browser will boot it. Mutation-verified: address a sibling instead of
   embedding, and it reports the CORS refusal.
3. **A shared export addresses the local runtime and nothing else.** A pinned
   jsDelivr URL was appended as a tail candidate on the same day and removed
   hours later, once the registry was checked: npm `@uibcdf/molsysviewer` is at
   `0.7.0` and this package at `0.20.0`, so the tail would have written a dead
   URL into other people's published pages. §3.6 already says the export refuses
   to write a URL it can predict is dead; the tail was that rule being broken by
   its own author. Reinstate it when publishing to npm is a standing release gate
   (`path_to_1_0.md` task 7) and not before. `shared_runtime="cdn"` is unaffected:
   an author who asks for the registry gets it, and gets the refusal if their
   version is unpublishable.

Two filed defects closed as consequences rather than as patches: the docs-lite
CDN pin and the standalone export mutating live widget state. Both are in
[`../archive/`](../archive/README.md).

Still open from this amendment: nothing blocks MolSysMT. The uncovered case —
many shared views opened offline from a disk — is parked with its research in
[`classic_script_runtime_for_offline_bundles.md`](../pending_proposals/classic_script_runtime_for_offline_bundles.md).
