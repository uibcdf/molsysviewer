# Response to the MolSysMT adoption report

**Status:** reply, 2026-08-04. Answers
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

## 3. Your camera diagnosis is wrong, and that is good news for the proposal

[`tight_initial_camera_framing_for_exported_views.md`](tight_initial_camera_framing_for_exported_views.md)
§2.2 says `export.html()` "serializes `camera.state` exactly as it exists in the
active view instance", so the export inherits a wide, unfocused camera.

Measured on our own published view (`docs/_static/views/demo_1TCD.html`), the
exported message list is:

```
load_molsys_payload, show_whole, set_sections, set_active_selection,
set_measurement_settings, update_visibility, set_trajectory_frame,
set_trajectory_playback, set_addon_runtime_summary
```

There is **no `set_camera_snapshot` at all**. A camera snapshot is requested from
the live frontend at export time; a script that never displayed the view has no
frontend to ask, so nothing is captured. Your export does not inherit a bad
frame — it inherits **no** frame, and what you see is the runtime's own framing
on load, evaluated against a 480 px iframe whose aspect ratio is nothing like the
notebook canvas the defaults were tuned for.

That matters because it moves the fix. Your Solution 1 (autofocus at export time)
cannot work: there is no camera state to correct. Your **Solution 2** — fitting
on load, in the runtime, where the real viewport is finally known — is the one
that addresses the cause.

**And a second measurement, which strengthens your case.** We checked whether an
author could work around this today by framing before exporting:

```python
view.camera.zoom(selection="all", extra_radius="1.0 angstroms")
view.export.html(...)
```

The zoom does **not** survive into the exported page. Camera is endpoint-local
state by Contract S9, and a static export is the deliberate exception only for a
snapshot captured from a live frontend. So there is currently **no way to frame a
view exported from a script**. That is a genuine gap, not a missing convenience,
and your report is what surfaced it.

**What you can do today**, until we fix it properly: frame it once by hand in a
notebook and carry the snapshot into your generation script.

```python
# once, in a notebook, after framing the view as you want it
view.camera.get_snapshot(pretty=True)      # copy the dict

# then, in docs/generate_static_views/1BRS_molecule_index_zero.py
view.camera.set_snapshot({...})            # paste it, before export.html(...)
view.export.html(...)
```

`set_snapshot` writes the snapshot Python-side, so it does reach the exported
page. It is a stopgap and we are not proud of it, but it works now.

## 4. What we are doing with your two proposals

We are treating
[`tight_initial_camera_framing_for_exported_views.md`](tight_initial_camera_framing_for_exported_views.md)
and
[`dark_light_theme_synchronization_and_transparent_canvas.md`](dark_light_theme_synchronization_and_transparent_canvas.md)
as **one piece of work**, because they collide in three places: both propose new
parameters on an `export.html` signature we deliberately collapsed to a single
argument last week, both act at the same moment in the runtime's boot, and both
are the same question in different clothes — *an exported view should adapt to
the frame it lands in*, in size and in theme.

Our starting suspicion, which the two proposals seen separately would hide: it is
possible that **neither should be an export parameter**. Framing belongs to the
scene, and theme belongs to the reading page, which can decide it in the browser
with `prefers-color-scheme` without the author baking a choice into the file at
export time. We will settle that before writing code.

Two notes on the theme proposal specifically, so you can weigh them:

- our on-canvas controls carry their own styling, tuned for a dark canvas. A
  transparent canvas over a light host page risks white on white;
- Mol\*'s depth and outline effects against a transparent background need to be
  looked at before we promise anything, and looking at them needs a real GPU.

Which is the honest limit on our side: we can verify what loads and what
properties get applied; whether it *looks* right is something we will need you or
Diego to confirm on a real screen.

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
