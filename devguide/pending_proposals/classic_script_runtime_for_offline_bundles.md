# A classic-script runtime, for the bundle nobody has asked for yet

**Status:** deliberately not done, 2026-08-04. This file exists so the day
somebody asks, the answer is already researched and measured rather than
rediscovered. Do not implement it without the trigger in §4.

**Origin:** while fixing "an exported view does not open from disk"
([`embedding_views_in_external_documentation.md`](embedding_views_in_external_documentation.md)),
this was the first design considered. A smaller change turned out to cover every
case anybody has today, so this one was parked with the measurements already
taken.

---

## 1. The one case that remains uncovered

A **directory of many shared views plus one runtime, opened with no server and
no network**. Supplementary material for a paper, downloaded as a zip; a USB
stick; an air-gapped review machine.

Today that reader must either serve the directory
(`python -m molsysviewer.preview`), or receive self-contained files, which
means one 6.4 MB runtime per view instead of one for all of them. Twelve views
is 77 MB instead of 7.

Everybody else is covered: a website is served, and a single file sent to a
colleague is self-contained and opens with a double click. (A pinned CDN tail
covered part of this for one day and was removed — npm is thirteen versions
behind, so it wrote a dead URL. It would not have covered the offline case
anyway.)

## 2. Why the shared shape cannot open from disk

Measured in Chrome 2026-08-04, on a real exported view:

| | result |
|---|---|
| default | `Access to script at 'file:///…/viewer.js' from origin 'null' has been blocked by CORS policy` |
| `--allow-file-access-from-files` | loads, no error |

A page opened from a disk is an opaque origin, and a **module** import across one
is refused. It is a browser policy, not a property of our code: QtWebEngine
enables the equivalent by default, which is why the Qt host and the headless
image export work from `file://` today with only a local candidate.

A **classic** `<script src>` is not subject to it. That is the whole mechanism of
this proposal, and it costs exactly one thing: a classic script cannot contain
`export`, so the bundle would stop being ESM.

## 3. What was measured, so it need not be measured again

`esbuild` with `format: "iife"`, `globalName: "MolSysViewerRuntime"` and a footer
assigning it to `globalThis`:

- **builds** — no top-level await anywhere in the bundle blocks it;
- **6.72 MB** against 6.40 MB for the ESM bundle, +5%;
- loaded from `file://` with `<script src>`: `bootDocsView` is a function,
  `default` an object — the global carries the same names the module namespace
  did, so consumers change *where* they read, not *what*;
- imported as a blob (the notebook's path): namespace has **0 keys**, and the
  global has `bootDocsView`, `default.render` and `MolSysViewerController`. So
  blob consumers keep `import()` and change the lookup;
- with `export default globalThis.MolSysViewerRuntime.default;` appended: imports
  as a module and yields `{render}`, which is what anywidget requires.

## 4. What would have to change, and the trigger

Five reading sites, one build script, one epilogue:

- `js/scripts/build-runtime.mjs` — format, global name, footer;
- `widget.py` bootstrap — read the global instead of the namespace. **Without
  this the notebook widget throws** ("does not export a render function"). Loud,
  not silent;
- `viewer/core.py::_build_lite_html` — load candidates with a `<script>` tag
  instead of `await import()`, walking them by events;
- `managers/popup-host.ts` (two loaders) and `popup/popup-logic.ts`, which
  already anticipates a `window.MolSysViewerController` path;
- wherever an ES module is *required* of the bundle, append the epilogue.

Costs that come with it, and are the reason this is parked:

- **the diagnostic gets worse.** `import()` rejects with a message; a script
  tag's `onerror` carries none. The failure text stays visible, the reason does
  not;
- **one global per document** where blob imports were isolated. Two runtime
  versions in one document would collide, which strengthens the case for
  [`exported_page_self_declaration.md`](exported_page_self_declaration.md);
- it moves the floor under all three hosts — notebook, popout, Qt — at once.

**Trigger:** a real user who needs many shared views to open with no server and
no network. Not a hypothetical one. Until then the preview server and the
self-contained export cover the ground, and `engineering_rules.md` §2 is easier
to honour on a bundle format nobody has had to migrate.
