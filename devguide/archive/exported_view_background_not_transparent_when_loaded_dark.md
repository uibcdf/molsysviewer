---
summary: An exported view embedded in a dark page renders opaque white instead of transparent.
issue: uibcdf/molsysviewer#34
status: resolved
opened: 2026-08-08
closed: 2026-09-02
severity: medium
verification: reproduced
area: [export, embedding]
guard: tests/test_export_runtime_source.py::test_an_embedded_transparent_page_declares_its_colour_scheme
normative:
blocked_by: []
supersedes: []
---

# An exported view loaded into a dark page is opaque white, not transparent

**Reported:** 2026-08-08, from MolSysMT, after its documentation was published for
the first time since January and the embedded `msm.view()` outputs were compared
against the local build.

**Status:** reproducible on demand, in two independent environments. The mechanism
is located but not proven; §5 says exactly which of two candidates it is and how to
tell them apart in minutes with the source at hand.

## 1. Affected contract

`view.export.html(..., background="transparent")` promises a view whose background
is transparent, so that an embedding page shows through it and the view therefore
follows the page's light/dark switch for free. That is the whole point of the mode:
**a transparent view needs no theme tracking at all**, because there is nothing of
its own to theme.

That promise holds only when the embedding page is in light mode at the moment the
iframe loads.

## 2. Reproduction

An exported view embedded in a Sphinx page built with `pydata-sphinx-theme` 0.20.0:

| Step | Result |
|---|---|
| Set the page to **light**, hard-reload | View background transparent. Switching the page to dark afterwards, the view follows. **Correct.** |
| Set the page to **dark**, hard-reload | View background **opaque white**. Switching light/dark afterwards changes nothing. **Wrong.** |

The variable is the page's theme *at load time*, not the theme afterwards.

Reproduced identically in two environments, which rules out the server and the
hosting path:

- locally, `python -m http.server --directory docs/_build/html`
- published, GitHub Pages at `http://www.uibcdf.org/molsysmt/`

## 3. Environment

- Export: `background="transparent"`, `shared_runtime` pointing at the shared
  `viewer.js`; the exported page's JSON config carries `"background_mode":"transparent"`.
- `scene_version` in the export: `0.20.0+131.g81b9d85f.dirty`.
- Runtime bundle: `viewer.js`, 6 409 528 bytes, md5 `e92001217938…`, byte-identical
  in the local build and on the published site.
- Embedding page: `pydata-sphinx-theme` 0.20.0, iframe same-origin with the page.

The exported HTML and the runtime are byte-identical between the working case and
the failing case. **Nothing about the artefact changes between the two; only the
page's theme at load time does.**

## 4. What is not the cause

The exported HTML makes the *document* transparent unconditionally when embedded,
without consulting any theme:

```html
<style>
  html, body { background: #fcfbf9; }
  @media (prefers-color-scheme: dark) { html, body { background: #101010; } }
</style>
<script>
  if (window.self !== window.top) {
    var sheet = document.createElement("style");
    sheet.textContent = "html, body { background: transparent !important; }";
    document.head.appendChild(sheet);
  }
</script>
```

So `html`/`body` are not the surface at fault, and neither is
`prefers-color-scheme`, which that `!important` rule overrides whenever the view is
embedded. What remains is the 3D canvas, painted by the runtime on top of the
document.

## 5. Where it happens

> **Superseded 2026-09-02. Everything in this section is refuted; it is kept because the
> refutation is the useful part.** The mechanism was never in `applyExportedBackground`,
> nor anywhere in the runtime, nor in Mol\*. See §9.



`applyExportedBackground(controller, mode)` in the runtime bundle, called from the
export bootstrap as
`applyExportedBackground(c, typeof ui.background_mode === "string" ? ui.background_mode : "auto")`.

Reconstructed from the bundle:

```javascript
function applyExportedBackground(controller, mode) {
  const transparent = mode === "transparent";
  let appliedDark, appliedColour;

  const paintSurface = (colour) => {
    const canvas3d = controller.plugin?.canvas3d;
    if (!canvas3d) return;
    if (transparent) {
      canvas3d.setProps({ transparentBackground: true });
    } else if (colour !== undefined) {
      canvas3d.setProps({ renderer: { ...canvas3d.props?.renderer ?? {}, backgroundColor: colour } });
    }
  };

  const paint = (dark, colour) => {
    if (dark === appliedDark) { paintSurface(colour); return; }
    appliedDark = dark;
    void Promise.resolve(controller.toggleBackground(dark ? "dark" : "light"))
      .then(() => paintSurface(colour));
  };

  const applyFromHost = () => {
    const colour = hostBackgroundColour(host);
    ...
    appliedColour = colour;
    paint(isDarkColour(colour), transparent ? undefined : colour);
  };

  applyFromHost();
  const observer = new MutationObserver(() => {
    for (const delay of [0, 120, 400]) window.setTimeout(applyFromHost, delay);
  });
  observer.observe(host.documentElement, { attributes: true });
  if (host.body) observer.observe(host.body, { attributes: true });
```

The channel by which the page's theme reaches the iframe is
`readableHostDocument()` plus `hostBackgroundColour(host)`: the iframe reads the
parent document — same origin — and walks up from `window.frameElement.parentElement`
until it finds an element with a non-transparent computed `backgroundColor`. The
`MutationObserver` on the host's attributes is what makes it follow the theme
switch, since the theme is an attribute flip on `<html>`.

**The defect is that this runs at all when `mode === "transparent"`.** `paint()`
calls `controller.toggleBackground("dark" | "light")` — asynchronous — and only
re-applies `transparentBackground: true` after it resolves. For a transparent
canvas the entire light/dark resolution is meaningless: there is no background of
its own to darken.

Two candidate mechanisms remain, and they are distinguished by one observation:

1. **`toggleBackground()` sets an opaque background whose effect lands after the
   promise resolves**, clobbering the `transparentBackground: true` applied in
   `paintSurface`. Under this reading the light case is not working either — it is
   opaque white on a white page, which is indistinguishable — and the "it follows
   the switch" observation is the toggle mirroring the host, not transparency.
2. **`toggleBackground("dark")` fails or resolves to a light preset**, leaving the
   canvas opaque white, and a later `applyFromHost` short-circuits at
   `if (colour === appliedColour) return;` so it never recovers.

**How to tell them apart:** load the failing case, open DevTools on the iframe
document and read the computed `background-color` of its `<html>`. Transparent
(`rgba(0, 0, 0, 0)`) means the CSS is fine and the canvas is the culprit —
candidate 1 or 2, both inside `applyExportedBackground`. A solid colour means the
`!important` rule lost, which would be a different defect in the export template.
Then set `transparentBackground` by hand on `canvas3d` from the console and see
whether the white disappears.

## 6. Recommended correction

When `mode === "transparent"`, skip the light/dark resolution entirely: do not call
`toggleBackground`, do not read the host colour, do not install the
`MutationObserver`. Set `transparentBackground: true` once, as soon as `canvas3d`
exists, and stop. A transparent canvas already follows the page by construction,
and every line that tries to help it do so is a line that can race with it.

This also removes the failure mode where the view depends on being able to read the
parent document, which a cross-origin embed would deny.

## 7. Acceptance tests

1. A view exported with `background="transparent"`, embedded in a page whose
   background is `#101010`, is transparent after a reload — verified by reading the
   canvas, not by eye.
2. The same view in a page whose background is white is *also* transparent, and is
   distinguishable from an opaque white canvas. The current light case passes by
   coincidence and must stop being the test that guards this.
3. Switching the embedding page's theme after load leaves the view transparent in
   both directions, with no reload.
4. A view exported with `background="transparent"` embedded **cross-origin**, where
   the parent document cannot be read, is still transparent.

## 8. Minimal reproduction, without Sphinx

```html
<!doctype html>
<html><body style="background:#101010;margin:0">
  <iframe src="1BRS_molecule_index_zero.html"
          width="100%" height="480" style="border:none"></iframe>
</body></html>
```

Served over HTTP next to the exported view and its `viewer.js`. Switching the body
background between `#101010` and `#ffffff` and reloading reproduces both cases with
no documentation toolchain involved.

---

## 9. Resolution — 2026-09-02

**The cause was outside both documents.**

The exported page never declared `color-scheme`. A document that declares none is treated
as **light**, and a light document whose `html` and `body` are transparent is painted over
the browser's own base canvas — which is **white**. Embedded in a light page that white
matches the host and nobody sees it; embedded in a dark one it is the opaque white
rectangle of §2.

The fix is one declaration, inside the branch that already runs only when the page is
embedded and transparent:

```css
html { color-scheme: light dark; }
```

`light dark` rather than a fixed value: an embedded document's used scheme follows its
embedder, so the base canvas now matches the host in both directions instead of trading
one wrong colour for another.

### What was refuted, and how

Both candidates in §5, and four more raised while chasing it. All were eliminated by
measurement in a real browser with the defect on screen:

| claim | how it fell |
| --- | --- |
| `toggleBackground` clobbers the transparency | `transparentBackground` read back **`true`** in the failing state |
| the `appliedColour` short-circuit prevents recovery | same — the flag was never lost |
| antialiasing or postprocessing suppress the transparent clear | both switched off live; still white |
| the WebGL context lacks alpha | `getContextAttributes().alpha` was **`true`** |
| the canvas is painting `backgroundColor` | set to pure green; **nothing changed on screen** |
| some element behind the canvas is white | every element from the canvas out to the host's `<body>` computed to `rgba(0,0,0,0)` |

The green test is the one that turned the investigation around. Once it was clear that
nothing in either DOM was painting the white, only the browser's compositing was left.

### The asymmetry in §2 did not reproduce

The behaviour follows the *current* theme, not the theme at load. Loading light and
switching to dark, or the reverse, both end in the same state. §2 is left as written
because it is what was observed then, and the discrepancy is itself worth knowing.

### Why no test could have caught this

Headless Chromium without WebGL flags renders the page's **init-failure overlay**, not the
scene, so pixel assertions there measure an error screen. With software WebGL
(`--use-angle=swiftshader`) the scene renders and the defect **does not appear** — the
transparent path behaves correctly. It needs a real GPU, which places this in the same
family as Phase 7's Qt observation in `what_needs_a_human_2026_08.md`: a defect only a
real browser on real hardware can see.

Guards: `test_an_embedded_transparent_page_declares_its_colour_scheme` and
`test_only_the_transparent_page_declares_a_colour_scheme`, both mutation-verified. They
pin the declaration and its scope — the other three background modes must not carry it,
since they paint their own opaque background and never expose the base canvas.

**All eleven static views under `docs/_static/views/` were regenerated**, because the fix
travels in the exported HTML and not in `viewer.js`: an already-exported view keeps the
defect until it is written again. MolSysMT carry the same kind of pre-generated views and
were told in `uibcdf/molsysmt#199`.
