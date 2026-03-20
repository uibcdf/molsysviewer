# Image Export Direction

This document records the current design direction for image export in
**MolSysViewer**.

It covers two related but distinct goals:

- **image export**
- **premium/publication-oriented image export**

The purpose is to keep this work aligned with the core identity of the project:

- a molecular workbench,
- reproducible scientific state,
- and a user experience that can support both exploration and communication.

## Core Position

MolSysViewer should support image export not merely as:

- "take a screenshot of the canvas"

but as:

- **export this scientific scene intentionally**
- **with this camera**
- **with this style**
- **with this visibility state**
- **with this output quality**

The export story should therefore be tied to:

- camera state
- style/preset
- visibility
- annotations
- measurements
- background
- and future figure-oriented recipes

## What We Mean By "Premium"

"Premium" image export does **not** mean:

- photorealism at any cost
- desktop-renderer complexity
- a noisy UI full of figure controls

It means:

- publication-quality clarity
- strong visual hierarchy
- deliberate composition
- clean silhouettes
- high-resolution output
- reproducible figure generation

The target is a figure that can stand in a paper, talk, or report without
feeling like an incidental screenshot.

## Current Technical Judgment About Mol*

After reviewing the local Mol* source tree, the current judgment is:

- **Mol* is not a hard limitation for high-quality figure export**

Why:

- it already has a serious screenshot/headless path
- it supports multisampling/image-pass rendering
- it supports postprocessing options such as:
  - occlusion
  - outline
  - shadow
  - antialiasing
  - sharpening/CAS
  - depth of field
  - fog
- it already includes stylized screenshot-oriented settings in its own codebase

So the main bottleneck for MolSysViewer is not "Mol* cannot render well enough".

The more likely bottlenecks are:

- missing publication-oriented styles
- missing export UX and API
- missing camera/composition workflows
- missing figure recipes/specifications
- missing curation of defaults

## The Real Opportunity For MolSysViewer

MolSysViewer can differentiate itself by combining:

- modern realtime rendering
- workbench interaction
- Python integration
- reproducibility
- and figure export based on the same scene model

This means the image-export story should not live outside the product.
It should be a natural extension of:

- `styles`
- `Navigate` / `Workbench`
- export/replay
- and future standalone/CLI directions

## Work Lines

The image-export direction should develop along several lines in parallel.

### 1. Basic Image Export

MolSysViewer should provide a simple but serious image export entrypoint.

Minimum expected features:

- export PNG
- explicit output size in pixels
- use current camera
- use current scene state
- allow background choice:
  - current
  - solid color
  - transparent

This is the minimum useful layer.

Current status:

- the first real slice now exists in the repository as Python `view.export.image(...)`
- current implemented scope:
  - PNG
  - optional `width_px` / `height_px`
  - optional `scale` multiplier for higher-resolution output
  - optional transparent background
  - live frontend required
- current implementation note:
  - it is backed by Mol*'s real viewport screenshot helper
  - not by a naive `canvas.toDataURL()` capture of whatever happens to be on screen

### 2. High-Resolution Export

High-quality figures need more than canvas capture.

The next level should support:

- supersampling or render scale
- high-resolution export factors such as:
  - `2x`
  - `4x`
  - perhaps later `6x`
- explicit width/height
- careful preservation of labels and linework

This is likely one of the highest-impact improvements.

### 3. Camera And Composition

Publication quality depends heavily on composition.

MolSysViewer should strengthen:

- persistent camera snapshots
- exact reuse of camera state
- explicit framing workflow
- perhaps later:
  - figure margins
  - crop intent
  - saved viewpoints

The figure should be reproducible as a composition, not just as raw pixels.

### 4. Publication Styles

MolSysViewer should eventually offer styles specifically oriented to figure
export.

These should not be mere structural presets.

They should include a more editorial visual direction:

- better contrast
- clearer focus/context hierarchy
- cleaner materials
- better silhouette separation
- more deliberate backgrounds
- less visual noise

This work should stay connected to the evolving `Style` model.

Candidate publication-oriented styles / looks worth exploring:

- `publication`
  - clean defaults for figures intended for papers and slides
- `illustrative`
  - stronger silhouette and shape separation, closer to explanatory figures
- `analysis`
  - slightly more technical and information-dense, but still cleaner than raw interactive defaults

### 5. Outlines, Occlusion, And Postprocessing

Mol* already suggests that this is a viable direction.

MolSysViewer should explore:

- subtle outline
- calibrated occlusion
- sharpening where useful
- maybe selective shadowing

But with a strong rule:

- postprocessing must support clarity
- not visual gimmickry

The aim is scientific legibility, not effect-heavy rendering.

Concrete Mol* capabilities worth exploiting here:

- headless screenshot
- multisampling / image-pass rendering
- outline
- occlusion
- CAS / sharpening

### 6. Labels And Annotations For Figures

Premium figures often fail because labels are weak, not because geometry is.

MolSysViewer should eventually improve:

- label contrast
- placement stability
- collision avoidance
- figure-oriented label styling
- consistent typography for export

This is likely a major differentiator for final figure quality.

### 7. Figure Recipes / Specifications

This is a particularly good fit for MolSysViewer.

The project should eventually be able to represent a figure not just as an
image file, but as a reproducible spec.

A future figure spec might include:

- camera
- style
- visibility
- annotations
- background
- image size
- scale factor
- maybe output intent

This is much more aligned with the project identity than raw screenshots alone.

### 8. Batch / Headless / Standalone Export

Later, image export should align naturally with:

- CLI launch
- standalone host
- headless export
- scripted figure generation

But this should come after the workbench and export model are mature enough.

## Output Formats

The output format story should remain staged.

Preferred first target:

- PNG

Likely later directions:

- TIFF if a stronger high-quality raster workflow becomes necessary
- helpers for external composition workflows
- future figure/session exports that combine image output with reproducible metadata

## Proposed Roadmap

The preferred roadmap is:

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

### Phase 4: Figure Spec

- reusable figure recipe
- reproducible export contract
- maybe batch export

### Phase 5: Host Expansion

- CLI export
- standalone export
- headless workflows

## Priority View

To avoid drift, it is useful to keep a very short priority map:

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

### Later

- `FigureSpec`
- batch export
- headless/CLI export
- possible future premium offline path

## Quick Wins

These likely offer the best return early:

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

The key is not the exact spelling yet.
The key is that the API should:

- be scriptable
- be reproducible
- and map naturally to the scene/workbench model

## Medium-Term Higher-Value Improvements

These are more strategic:

- figure recipe/spec model
- publication-oriented label system
- reusable scene/look presets for figure generation
- export API that is equally usable from:
  - notebook
  - script
  - future standalone host

## Things To Avoid

This direction should avoid:

- screenshot-only thinking
- many ad hoc export toggles in the visible canvas UI
- postprocessing as spectacle
- a giant "figure settings" panel too early
- creating a figure export pipeline disconnected from the scene/state model

The export story should stay:

- minimal in visible UX
- strong in reproducibility
- progressive in complexity

## Risks And Frictions

Some quality problems are likely to appear before the system feels mature.

The main risks worth tracking are:

- labels:
  - they can easily become the weakest part of figure quality
- transparent backgrounds combined with outline/fog:
  - these combinations often look worse or behave differently than expected
- confusing screenshot export with reproducible figure export:
  - these should remain related, but not conceptually collapsed into the same thing

## Relation To The UI Direction

The current minimal canvas philosophy still applies.

Image export should not force:

- toolbar clutter
- permanent figure buttons everywhere
- a noisy canvas

The likely future interaction model remains consistent:

- quick export actions from the menu or panel
- deeper figure/export configuration in `Workbench`
- scripted/export-heavy use from Python or future CLI

## Relation To `Workbench`

The current `Workbench` direction already suggests where image export should
live in the interactive UX.

Most likely:

- `Scene` becomes the first visual home for export-related controls
- quick export actions remain small and unobtrusive
- deeper figure/export configuration should appear in `Workbench`, not as
  permanent canvas clutter

This keeps the canvas calm while still making export a first-class capability.

## Open Questions

These questions are worth tracking, but should not be answered too quickly:

- what should be the first public image export API:
  - `view.export.image(...)`
  - `view.figures.export(...)`
  - both eventually
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
- whether MolSysViewer should support saved figure recipes as first-class
  artifacts

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
