# Response to the MolSysMT adoption report

**Status:** closed 2026-08-05. Both proposals answered, one archived without a
change and one delivered and adopted. Kept here because it is the record of what
was measured; the durable descriptions live in the user guide.

Answers
[`molsysmt_embedding_feedback_and_transparent_adapter_pattern.md`](molsysmt_embedding_feedback_and_transparent_adapter_pattern.md).

**Audience:** the MolSysMT team. Everything here is either something we changed
on our side because of your report, something we would change on yours, or a
measurement that contradicts one of your conclusions.

**First, the part that matters most:** you are the first external adopter of this
mechanism and you built it correctly, from a specification that until three days
ago described a path we did not run ourselves. The pre-generation script, the
`builder-inited` hook, the gitignored runtime and `nb_execution_mode = "off"` are
exactly the intended shape.

---

## 1. What we changed because of your report

**Your §4.4 describes a workaround for a defect, not a usage tip.** You wrote
that passing `skip_digestion=True` "ensures smooth execution across varying input
formats" when calling `embed_iframe(..., width="100%")`.

It was not smoothness. `width` is a **physical length** everywhere else in
MolSysViewer — shapes, boxes — and its digester expects a quantity in units, so
it rejected the CSS string `"100%"`, which is `embed_iframe`'s own default. The
documented call raised.

It was invisible to us for two reasons worth naming, because they are the kind of
blind spot that repeats: all four of our tests passed `skip_digestion=True` and
so never crossed the argument layer, and every example in the user page is a
markdown cell, which Sphinx does not execute.

Fixed in `c3695273`: the digester now answers the CSS question for this caller
and the length question everywhere else, and it also accepts `width=600` as
pixels. **Drop `skip_digestion=True` from your adapter.** It is worth dropping
for its own sake: it also switches off validation of `filename` and `path`, so a
mistyped view file currently reaches `embed_iframe` unchecked.

## 2. Your code is ahead of your report

We read `molsysmt/basic/viewer/molsysviewer.py` and `docs/conf.py` rather than
only the report, and two of the three things we were going to raise are already
fixed there:

- the adapter **consumes** the target (`f_locals.pop(...)`), so a later cell
  cannot silently inherit an earlier cell's view;
- and it **raises** when no target is in scope instead of falling through to a
  live widget that could never render in a static page. `conf.py` no longer
  swallows the runtime-placement error either.

Both are the right calls. The report describes an earlier version; worth
knowing, because we were about to send you advice you had already taken.

Three things do remain.

### 2.1 `nb_path` is right only for `docs/index.ipynb`

```python
nb_path = f_locals.get('__file__', 'index.ipynb')
```

`__file__` is not defined in a notebook's globals, so this is always the
fallback, and the fallback asserts that the page lives at `docs/index.ipynb`. It
works in the pilot because both paths are named from the same directory and the
common prefix cancels — that is by design in `embed_iframe`, the two arguments
only have to share a frame of reference.

It breaks on the **first notebook in a subdirectory**. `nbconvert` runs a
notebook with the working directory set to that notebook's own folder, so
`Path(htmlfile).is_file()` will be false for a `_static/views/...` written
relative to `docs/`, and your `RuntimeError` will fire on a notebook that is
correctly configured. Since the next thing you do is migrate the other 68
notebooks, this is the one to fix first.

The robust form is to stop inferring it: put the notebook's own path in the
hidden cell beside the view, or derive both from a documentation root you
compute once.

### 2.2 `f_locals.pop` works for a reason worth knowing

`frame.f_locals` is the real dictionary only for module-level frames. Notebook
cells are module-level, so the `pop` sticks. In a function frame — if the call
were ever wrapped in a helper that defines the variable locally — the mutation
would be discarded silently on Python below 3.13. It is correct today; it is
correct by circumstance rather than by construction.

### 2.3 `conf.py` still registers require.js and nglview from CDNs

```python
app.add_js_file('https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js')
app.add_js_file('https://cdn.jsdelivr.net/npm/nglview-js-widgets@3.1.0/dist/index.js')
```

We removed exactly these two from our own `conf.py` as vestigial. For you they
may still be load-bearing: 26 notebooks still carry `nglview_htmlfile`, and any
page with a live NGLView widget state needs them. Worth deciding deliberately
rather than by inertia — while the migration runs they stay; when the last
nglview output goes, so do they, and every page in the site stops fetching two
scripts from two third-party hosts.

### 2.4 Your environment files do not reproduce your working setup

`devtools/conda-envs/{production,development,test,docs}_env.yaml` all declare a
bare `molsysviewer` dependency. On the machine where this was built that resolves
to nothing, because MolSysViewer is a local development install in the shared
conda environment — so everything works and nothing warns.

Anyone creating one of those environments from scratch — a new contributor, CI,
a rebuilt machine — gets the conda package instead. Checked today: `uibcdf`
serves **molsysviewer 0.7.0**, and it is not on PyPI at all. Thirteen versions
behind, and old enough to predate `shared_runtime`, `export_runtime_asset` and
`tools.embed_iframe` entirely. That environment cannot build your documentation,
and the error it gives will point at the wrong thing.

This is ours as much as yours — the conda channel being thirteen versions stale
is our release discipline, the same gap as the unpublished npm package. But
until a current release exists, your environment files should say so: pin the
development install, or note in the docs environment that MolSysViewer must come
from a checkout.

## 3. The framing: measured, and there is nothing to fix

We rendered the page you were looking at — `docs/_build/html/index.html`, barnase
in its 946x480 embed — in a real browser, and measured the pixels.

**Your observation is exact.** The molecule is 342 x 247 px: **51 % of the
height**, 36 % of the width. "~30–40 % of the viewport" was a good eye.

**Your explanation is not, and neither was our first one.** Three findings, in
the order they arrived:

1. **The export is not involved.** §2.2 of your proposal says `export.html()`
   serialises the camera state as it stands. There is no camera state to
   serialise: a script that never displayed the view has no frontend to ask, and
   your exported view carries no `set_camera_snapshot` at all. Whatever you see
   is the runtime framing the scene on load.

2. **Nor is the embed.** We measured the same view at three canvas shapes:
   51 %, 51 % and 52 % of the height at 1.97:1, 1.40:1 and 1:1. The framing is
   identical everywhere; what changes is the empty width around it — 36 %, 51 %,
   71 % of the width. A notebook widget is framed exactly the same and merely
   reads as fuller. So there is no "exported views need different framing"
   problem to solve.

3. **Mol\* is not being wasteful.** It places the camera at `r / sin(fov/2)`, so
   the bounding sphere exactly fills the height. We first thought there was a
   further 25 % unaccounted for; Diego pointed out that we were comparing against
   a sphere Mol\* does not use — its sphere is built from the rendered geometry
   and includes the representation's radii. Checking against your coordinates
   settles it: 51 % of the height would imply a projected extent of 24.0 A over a
   23.4 A atom-centre sphere, and the smallest extent this molecule can present in
   *any* orientation is 25.4 A. The measurement is only consistent with a bigger
   sphere. There is no gap, and nothing is broken.

**What is actually going on** is worth knowing, because it is not a defect and it
explains everything: a molecule's projected extent runs between **0.54 and 0.95**
of its bounding sphere's diameter depending on which way it faces, and your view
sits at the narrow end. The camera starts aligned with the world axes, so the
orientation you get is whatever frame the structure file carried. Barnase drew a
bad one; another entry would have looked fine with the same code.

**So the proposal is closed without a change**, and archived with the
measurements. Two practical notes for you meanwhile:

- if a particular figure deserves a tighter frame, compose it once in a notebook
  and carry the camera into your generation script — `view.camera.get_snapshot(pretty=True)`
  there, `view.camera.set_snapshot({...})` before `export.html(...)` here. That is
  the only way today to frame a view exported from a script, and it is a real gap
  we are not proud of;
- the iframe's shape is yours to choose and it is what governs how empty the
  result reads. `msv.tools.embed_iframe(..., height="600px")` on a ~950 px column
  goes from 1.97:1 to 1.58:1, which is the cheapest improvement available to you
  and costs nothing.

There is one lever we deliberately did **not** pull: `orientAxes()`, Mol\*'s own
principal-axis alignment, would turn the molecule to face the screen with its
broad side and move that 0.54 towards 0.95 — up to 1.75x more molecule, using
their machinery, with no change to the camera distance. We left it alone because
it would change the default orientation of every view in every notebook, and
nothing is broken. It is recorded in the archived proposal if the question comes
back.

## 4. The theme proposal: done, and it needs nothing from you

`export.html` takes one new argument. It is the only one this work added, and it
exists because the choice it expresses cannot be made where the file is written:
an exported view is read on somebody else's page, on a screen its author never
saw.

```python
view.export.html(path, background="auto")         # default
view.export.html(path, background="transparent")
view.export.html(path, background="white")        # or "dark"
```

| value | what the page sits on |
|---|---|
| `"auto"` *(default)* | the background of the page it is embedded in, copied exactly, and followed when that page changes. Falls back to the reader's light/dark preference when there is no host to ask. |
| `"transparent"` | nothing: the canvas clears with alpha and the host shows through. For a host whose background is a gradient or an image, where copying a colour is not enough. |
| `"white"` / `"dark"` | fixed, ignoring host and reader alike. |

### Why `"auto"` follows your theme switch without you writing anything

Your proposal's Solution 2 has the host broadcast `MSV_SET_THEME` to every
iframe. It is not needed, and we checked rather than assumed: in the
`pydata-sphinx-theme` you ship, `postMessage` appears **zero** times, and so do
`dispatchEvent` and `CustomEvent`. There is no emitter. Adopting Solution 2 would
mean *writing* one into your templates and maintaining it against the theme's
releases.

What the theme does do, on every toggle, is write `data-theme` and `data-mode`
onto `<html>`. And a view is served from the same site as the page embedding it,
so the two are same-origin and the view can simply read that document. So it
does:

1. reads the host's computed background colour and uses it as the canvas colour —
   the exact value, not our nearest approximation;
2. picks the lighting by its luminance, because dark mode is also a white key
   light and a molecule lit for a bright page reads badly on a dark one;
3. watches the host's `<html>` and `<body>` attributes with a `MutationObserver`,
   which is precisely where your theme writes, and re-reads on change. It costs
   nothing while nothing changes — it is a callback, not a poll — and it repaints
   only when the colour actually moved.

Measured: on a `#1a1a1a` host the canvas comes out `(26,26,26)`; on `#ffffff` it
comes out `(255,255,255)`. The dark case was produced by flipping `data-theme` at
runtime with the *system* preference left on light — your toggle, in other words.

**Limits, stated plainly.** It needs same-origin, which every published site is,
but two files opened from a disk are not — there it falls back to the reader's
preference. It reads a colour, so a gradient or image background falls back too;
that is what `"transparent"` is for. And it reacts rather than being correct by
construction: there is a small lag after your theme animates, where
`"transparent"` cannot desynchronise because it has nothing to synchronise.

### What we need you to test

We can measure pixels; we cannot judge whether it looks right. Four things, and
the second is the one that matters:

1. **Generate both.** One line in
   `docs/generate_static_views/1BRS_molecule_index_zero.py`:

   ```python
   view.export.html(str(views_dir / "1BRS_auto.html"),
                    shared_runtime=str(static_dir), background="auto")
   view.export.html(str(views_dir / "1BRS_transparent.html"),
                    shared_runtime=str(static_dir), background="transparent")
   ```

   Point the hidden cell in `docs/index.ipynb` at one, then the other, and
   rebuild. Nothing else changes: your `conf.py` places the runtime as it does
   today.

2. **Flip your theme switch with your system on the opposite setting.** Site to
   dark while the OS is light. This is the case that separates the two, and the
   case your original report was about. Both should follow; tell us if either
   does not, or if the transition looks wrong while the theme animates.

3. **Look at what we cannot.** With `"transparent"`: the molecule's edges against
   your theme's colour, how the depth fog reads with nothing behind it, and
   whether the on-canvas controls in the top right survive a light background —
   they are styled for a dark canvas and that is our main worry.

4. **Open one view as a plain file**, not through the site, and check it still
   has a sane background. That path cannot read a host and falls back to your
   system preference.

Then tell us which of the two you would keep. If `"auto"` covers you, that is one
fewer thing for an author to decide; if `"transparent"` reads better on your
theme, we would rather know before anybody else adopts this.

One practical note: two views means two ~150 KB files tracked in git. Delete the
one that does not survive.

## 5. What a shared export addresses, and what it does not

Your published pages should contain exactly one runtime reference: the relative
path to `viewer.js` beside them. No registry URL, no fallback, nothing that can
rot while your site is up.

That is worth stating because for a few hours on 2026-08-04 it was not true. We
appended the pinned jsDelivr URL as a last-resort candidate, meaning to rescue a
view opened straight from a disk. Then we checked the registry: npm
`@uibcdf/molsysviewer` is at **0.7.0** against MolSysViewer's `0.20.0`, so that
tail 404s for every release it would have served — a dead URL written into other
people's pages by the same design whose stated rule is that the export refuses to
write a URL it can predict is dead. Removed the same day.

Nothing you have published is affected either way: if you export from a git
checkout, no tail was ever written; if you export from a release, regenerating
your views on a current MolSysViewer removes it.

The registry remains available to anyone who asks for it explicitly —
`shared_runtime="cdn"` — and refuses to write anything if the exporting version
is not publishable. We will reinstate the automatic fallback when publishing to
npm is a standing release gate on our side, which is our task, not yours.


---

## 6. Outcome, 2026-08-05

MolSysMT replied to §4 having tested the three things we could not judge: depth
fog, molecular edges and the on-canvas controls over a light background all read
cleanly. **They adopt `background="transparent"` for their documentation** and
recommend keeping both values, which we have.

They also reported the one property that separates them, and it is the property
this design predicted rather than measured until now: `"transparent"` turns with
the page instantly, because there is nothing of ours to change, while `"auto"`
blinks perceptibly as the observer fires and the canvas repaints. Correct by
construction against correct by reaction. That distinction is now the guidance in
the user page — `"transparent"` on a site, `"auto"` for a file that travels
alone — and the reason to keep both rather than pick one.

Both of their proposals are closed:
[the framing one](../archive/tight_initial_camera_framing_for_exported_views.md)
without a change, measured and found correct; and
[the theme one](../archive/dark_light_theme_synchronization_and_transparent_canvas.md)
delivered under one argument, with its Solution 2 — a `postMessage` protocol —
shown to be unnecessary.
