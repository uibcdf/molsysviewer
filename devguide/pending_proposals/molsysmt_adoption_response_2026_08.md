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

## 2. Three things we would change in your integration

### 2.1 `conf.py` succeeds when the runtime is missing

```python
def _place_runtime(app):
    try:
        ...
        export_runtime_asset(...)
    except Exception as e:
        print(f"Warning: Could not export MolSysViewer runtime asset: {e}")
```

If that call fails, the build **succeeds** and you publish a site whose every
view is a blank frame. That is precisely the failure class we spent this week
removing from our own docs — a green build producing a broken site — and it is
the one defect this whole mechanism exists to make impossible.

Let it raise. `export_runtime_asset` already fails with a message naming the
directory and the reason (`NotADirectoryError` if `_static` is not there,
`FileNotFoundError` if the installed package has no runtime, `FileExistsError` if
something that is not ours already occupies `viewer.js`). A build that cannot
place the runtime should stop.

### 2.2 The hidden variable is shared by every cell of the notebook

Your adapter looks for `molsysviewer_htmlfile` by walking the caller frames.
Notebook cells share one globals dictionary, so the variable set in cell 5
survives for the rest of the notebook. With one view per notebook this is
invisible. With two, any `msm.view()` whose hidden cell was forgotten will
silently embed **the previous view** — the build succeeds, the page renders, and
the wrong molecule is on it.

Two cheap defences, either of which is enough:

```python
# in the adapter, after resolving it
f_locals.pop('molsysviewer_htmlfile', None)      # consume it
```

or make it fail loudly instead of falling back:

```python
if os.environ.get("MSM_VIEWS_FROM_HTML_FILES", "").lower() == "true":
    ...
    raise RuntimeError(
        "msm.view() was called in static documentation mode with no "
        "molsysviewer_htmlfile in scope. Add the hidden cell, or the page will "
        "embed a view belonging to another cell."
    )
```

The second is better: in documentation-build mode, falling through to a live
widget produces a cell whose output can never render anyway.

### 2.3 `nb_path` assumes the notebook lives in `docs/`

```python
nb_path = f_locals.get('__file__', 'index.ipynb')
```

`__file__` is not defined in a notebook's globals, so this is always the
fallback, and the fallback says "the page is `docs/index.ipynb`". It works today
because both paths are named from the same directory and the common prefix
cancels — that is by design in `embed_iframe`, both arguments only have to share
a frame of reference.

It stops working for a notebook in a subdirectory: `Path(htmlfile).is_file()`
will be false (the relative `_static/views/...` no longer resolves from there),
the adapter falls through to the live-widget path, and you get a cell with no
usable output. With 746 notebooks, that will be soon.

Suggestion: set the notebook's own path in the hidden cell alongside the view, or
derive both from a known documentation root, so the pair is always explicit
rather than inferred.

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

## 5. One thing you should know about the pages you have already published

Since 2026-08-04 an export from a **released** MolSysViewer appends the pinned
jsDelivr URL as a last-resort candidate, tried only after the local runtime fails
— which on a served site never happens.

Measured today: npm `@uibcdf/molsysviewer` is still at **0.7.0**, so for anyone
exporting from a released 0.20.0 that tail URL 404s. It is inert on your
published site (the local runtime answers first and the tail is never fetched),
but it is a dead URL sitting in your HTML, and by our own rule — *the export
refuses to write a URL it can predict is dead* — it should probably not be there
until publishing to npm is a real release gate. That decision is ours to make and
it is open; you do not need to do anything, and nothing you have published is
broken by it.

If you export from a git checkout of MolSysViewer, this does not apply at all:
development versions get no tail.
