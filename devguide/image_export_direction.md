# Image Export Direction

This document records the current design direction for image export in
**MolSysViewer**, covering both ordinary export and premium, publication-oriented
export. It exists to keep that work aligned with what the project is: a molecular
workbench with reproducible scientific state, whose UX has to serve exploration
and communication alike.

## Core Position

Export is not "take a screenshot of the canvas". It is **export this scientific
scene intentionally** — with this camera, this style, this visibility state and
this output quality. So the export story is tied to camera state, style/preset,
visibility, annotations, measurements, background, and the figure recipes that
come later.

## What We Mean By "Premium"

Not photorealism at any cost, not desktop-renderer complexity, and not a UI full
of figure controls. It means publication-quality clarity: strong visual
hierarchy, deliberate composition, clean silhouettes, high-resolution output and
reproducible figure generation. The target is a figure that can stand in a paper,
a talk or a report without looking like an incidental screenshot.

## Current Technical Judgment About Mol\*

After reviewing the local Mol\* source tree: **Mol\* is not a hard limitation for
high-quality figure export.** It already has a serious screenshot/headless path,
multisampling and image-pass rendering, postprocessing (occlusion, outline,
shadow, antialiasing, sharpening/CAS, depth of field, fog), and stylized
screenshot-oriented settings of its own.

The bottleneck is ours, not the renderer's: missing publication-oriented styles,
missing export UX and API, missing camera and composition workflows, missing
figure recipes, and uncurated defaults.

## The Real Opportunity For MolSysViewer

The differentiator is the combination — modern realtime rendering, workbench
interaction, Python integration, reproducibility, and figure export built on the
*same scene model*. So image export should not live outside the product: it is a
natural extension of `styles`, the panel surface, export/replay, and the
standalone/CLI directions.

## Work Lines

The image-export direction should develop along several lines in parallel.

### 1. Basic Image Export

A simple but serious entrypoint: PNG, explicit output size in pixels, the current
camera and scene state, and a background choice between current, a solid colour
and transparent. That is the minimum useful layer.

**Status: the first slice exists** as `view.export.image(...)`, covering PNG,
optional `width_px` / `height_px`, an optional `scale` multiplier, and a
transparent background. It requires a live frontend, and it is backed by Mol\*'s
real viewport screenshot helper rather than a naive `canvas.toDataURL()` capture
of whatever happens to be on screen.

### 2. High-Resolution Export

Good figures need more than canvas capture: supersampling or render scale,
export factors like `2x` and `4x` (perhaps `6x` later), explicit width and
height, and careful preservation of labels and linework. Likely one of the
highest-impact improvements.

### 3. Camera And Composition

Publication quality depends heavily on composition, so persistent camera
snapshots, exact reuse of camera state and an explicit framing workflow matter —
with figure margins, crop intent and saved viewpoints as later candidates. The
figure should be reproducible *as a composition*, not just as raw pixels.

### 4. Publication Styles

Styles oriented specifically to figure export, not merely structural presets:
better contrast, a clearer focus/context hierarchy, cleaner materials, better
silhouette separation, more deliberate backgrounds, less visual noise. This stays
connected to the evolving `Style` model.

Candidate looks: `publication` (clean defaults for papers and slides),
`illustrative` (stronger silhouette and shape separation, closer to explanatory
figures), and `analysis` (more technical and information-dense, but still cleaner
than raw interactive defaults).

### 5. Outlines, Occlusion, And Postprocessing

Mol\* already shows this is viable, and it exposes what is needed: headless
screenshot, multisampling and image-pass rendering, outline, occlusion, and
CAS/sharpening. Worth exploring subtle outline, calibrated occlusion, sharpening
where useful and perhaps selective shadowing — under one rule: **postprocessing
must support clarity, not visual gimmickry.** The aim is scientific legibility,
not effect-heavy rendering.

### 6. Labels And Annotations For Figures

Premium figures usually fail on labels, not on geometry. Improving label
contrast, placement stability, collision avoidance, figure-oriented styling and
consistent typography for export is likely a major differentiator for final
figure quality.

### 7. Figure Recipes / Specifications

A particularly good fit for this project: representing a figure not just as an
image file but as a **reproducible spec** — camera, style, visibility,
annotations, background, image size, scale factor, perhaps output intent. That is
far more aligned with the project's identity than raw screenshots.

### 8. Batch / Headless / Standalone Export

Later, export should align with CLI launch, the standalone host, headless export
and scripted figure generation — after the workbench and export model are mature
enough.

## Output Formats

Staged. PNG first. Later, TIFF if a stronger high-quality raster workflow becomes
necessary, helpers for external composition workflows, and figure/session exports
that combine image output with reproducible metadata.

## Proposed Roadmap

### Phase 1: Essential Export

- `view.export.image()`
- PNG
- explicit size
- current camera
- current state
- solid/transparent background

### Phase 2: High-Quality Export

- render scale / supersampling
- better quality defaults
- camera reproducibility
- cleaner scene-state capture
- first export-oriented preset surface:
  - `current`
  - `publication-light`
  - `publication-dark`

### Phase 3: Publication Export

- `publication_style`
- outline/occlusion tuning
- better label treatment
- explicit figure-oriented presets
- first explicit `view.export.figure()` wrapper above raw image export

### Phase 4: Figure Spec

- reusable figure recipe
- reproducible export contract
- maybe batch export

### Phase 5: Host Expansion

- CLI export
- standalone export
- headless workflows

## Priority View

A short priority map, to avoid drift.

### Now

- real `view.export.image()` API
- PNG
- explicit size
- transparent/solid background
- camera snapshot reuse
- supersampled export

### Next

- `publication_style`
- first export-oriented scene presets
- stronger label treatment
- figure-oriented export defaults
- richer export presets beyond background-only capture control
- stronger `figure` wrapper semantics beyond simple image capture

### Later

- `FigureSpec`
- batch export
- headless/CLI export
- possible future premium offline path

## Quick Wins

Best return early:

- real `view.export.image()` API
- transparent background export
- supersampled export
- camera snapshot reuse
- first reversible export preset surface
- first `publication` scene style

These are much more valuable than trying to solve every figure problem at once.

## Candidate Public APIs

The exact API should remain open for a little while longer, but the likely
public directions are already visible.

Examples worth keeping in mind:

```python
view.export.image("figure.png", width_px=2400, height_px=1800, transparent=True)
```

and later perhaps:

```python
view.figures.export(
    "figure.png",
    style="publication",
    camera="current",
    background="white",
    scale=4,
)
```

Current practical bridge state now also includes:

```python
view.export.figure(
    "figure.png",
    width_px=2400,
    height_px=1800,
    background="white",
    preset="publication-light",
    scale=2.0,
)
```

This is not yet the final figure system. It is the first explicit wrapper that
maps a figure-oriented request onto the current image export runtime.

There is now also a first minimal reusable recipe object:

```python
from molsysviewer import FigureSpec

spec = FigureSpec(
    width_px=2400,
    height_px=1800,
    scale=3.0,
    background="dark",
    preset="publication-dark",
)

view.export.figure("figure.png", figure_spec=spec)
```

This is still intentionally small. It is not yet a rich figure project format,
but it already proves that figure export can start to become reusable without
disconnecting from the current scene/export runtime.

The recipe layer has now grown one more useful step:

```python
spec = FigureSpec.from_view(
    view,
    width_px=2400,
    height_px=1800,
    preset="publication-light",
)

alt = spec.with_overrides(background="transparent")

view.export.figure("figure.png", figure_spec=spec)
view.export.figure("figure-transparent.png", figure_spec=alt)
```

This matters because the first reusable figure story should be:

- derive a recipe from a real viewer state
- keep camera/state reuse explicit
- generate small figure variants without rebuilding everything by hand

The next practical layer now also exists:

```python
base = FigureSpec.from_view(view, width_px=2400, height_px=1800)
variants = base.build_variants(
    {
        "dark": {"background": "dark", "preset": "publication-dark"},
        "transparent": {"background": "transparent"},
    }
)

view.export.figure_variants("figures/", variants=variants, stem="pocket")
```

This is still intentionally modest:

- it is directory-oriented
- it expects explicit named `FigureSpec` recipes
- and it keeps the batch story tied to the same reproducible export surface

There is now also a first built-in publication bundle:

```python
base = FigureSpec.from_view(view, width_px=2400, height_px=1800)

view.export.figure_publication_set(
    "figures/",
    figure_spec=base,
    stem="binding-site",
    include_current=True,
)
```

That bundle is intentionally small and concrete:

- `light`
- `dark`
- `transparent`
- optional `current`

So the current figure story now has three levels:

- one figure
- a named custom batch
- a standard small publication bundle

The key is not the exact spelling yet.
The key is that the API should:

- be scriptable
- be reproducible
- and map naturally to the scene/workbench model

## Medium-Term Higher-Value Improvements

More strategic: a figure recipe/spec model, a publication-oriented label system,
reusable scene/look presets for figure generation, and an export API equally
usable from a notebook, a script and the standalone host.

## Things To Avoid

Screenshot-only thinking; many ad hoc export toggles in the canvas UI;
postprocessing as spectacle; a giant "figure settings" panel too early; and a
figure pipeline disconnected from the scene/state model. The export story stays
minimal in visible UX, strong in reproducibility, progressive in complexity.

## Risks And Frictions

Three quality problems will appear before the system feels mature. **Labels** can
easily become the weakest part of a figure. **Transparent backgrounds combined
with outline or fog** often look worse, or behave differently, than expected. And
**screenshot export and reproducible figure export** are related but must not
collapse into the same concept.

## Relation To The UI Direction

The minimal canvas philosophy still applies: no toolbar clutter, no permanent
figure buttons, no noisy canvas. Quick export actions belong in the menu or the
panel, deeper figure configuration in the Studio's export subpanel, and
export-heavy use in Python or the CLI. `Export` is a Studio subpanel today, which
is where the earlier drafts of this document expected "deeper configuration" to
land.

## Open Questions

These questions are worth tracking, but should not be answered too quickly:

- ~~what should be the first public image export API~~ — **answered by what
  shipped:** `view.export.image(...)`, alongside `view.export.figure(...)`,
  `figure_variants(...)` and `figure_publication_set(...)`. `view.figures.export`
  was not adopted. Left visible rather than deleted so the discarded branch stays
  legible.
- should the first export target be only PNG, or also SVG/PDF-friendly
  helper paths for labels/overlays later
- how should transparent background interact with outlines and fog
- how much postprocessing should be enabled by default in publication export
- should "premium" export use a dedicated style, or a style plus export preset
- how much of figure export belongs in:
  - `Style`
  - camera snapshots
  - a future `FigureSpec`
- how should export work in future standalone/CLI mode
- ~~whether MolSysViewer should support saved figure recipes as first-class
  artifacts~~ — **answered: yes.** `FigureSpec` exists, `FigureSpec.from_view()`
  captures the current camera, `view.set_figure_spec()` anchors the recipe to the
  workbench, and `build_variants()` derives named batches. See `smoke_test.md`
  §12 for the exercised flow.

## Acceptance Criteria For The First Serious Export Slice

The first export slice should probably be considered successful only if it can:

- export a PNG reliably from the current scene
- preserve the current camera
- optionally accept an explicit saved camera snapshot for reproducible figure
  generation
- support explicit output size
- support transparent or solid background
- produce visibly better results than a naive browser screenshot when using
  higher scale
- remain scriptable from Python without UI-only assumptions

## Future Direction Towards Offline Rendering / Ray Tracing

This direction should be kept open, but treated as a later and more expensive
path.

Current judgment:

- a more classical offline-rendering or ray-tracing-oriented path is
  conceptually possible
- but it would not be a natural small extension of the current Mol* runtime

Why:

- Mol* is primarily a realtime rendering engine
- its current strength is strong interactive rendering plus screenshot/export
- offline or ray-traced rendering would likely require:
  - a substantially new rendering path inside Mol*
  - or an export bridge from MolSysViewer/Mol* scene state to another renderer

So the future options are roughly:

### 1. Deeper rendering path inside Mol*

- technically possible in principle
- expensive
- architecturally invasive
- unlikely to be the first sensible direction

### 2. Export bridge to an offline renderer

- technically possible in principle
- would require translating:
  - geometry
  - camera
  - visibility
  - materials/look
  - labels/annotations or figure overlays
- more plausible than rebuilding Mol* itself, but still a serious project

### 3. Hybrid strategy

- keep Mol* for interaction and most figure export
- later add a premium offline export path for selected scenes
- likely the most realistic long-term variant if this direction ever becomes necessary

Important conclusion:

- this path should not drive near-term decisions
- MolSysViewer still has a large amount of quality headroom to explore on top of
  the current Mol* rendering pipeline
- offline/ray-tracing should therefore be considered a future expansion path,
  not the current answer to figure quality

## Provisional Conclusion

MolSysViewer should definitely grow an image-export line.

And it should grow it in two steps:

1. reliable image export
2. premium/publication-oriented export

The engine base (Mol*) appears good enough for this to be worthwhile.

So the strategic challenge is not primarily rendering capability.
It is building the right:

- styles
- export contract
- camera/composition workflow
- and figure-oriented reproducible product layer

That is where MolSysViewer can get close to premium figure quality without
losing its own identity.
