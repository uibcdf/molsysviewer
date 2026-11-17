(User_Movie)=
# Movie

`view.movie` lets you define a keyframe timeline, preview it in the browser,
and export it from a Python notebook.

A movie uses a specific view's camera, regions, layers and structures. Save its
timeline as a JSON recipe to replay it on a compatible view.

MolSysViewer 0.24.0 provides version-1 keyframes and synchronous video and GIF
export. The development version adds experimental version-2 independent
tracks, Studio authoring, and MP4, WebM, lossless PNG ZIP and offline HTML
export. See {doc}`export` for the requirements of each workflow.

## When to use `view.movie`

Use `view.movie` when you need to:

- record a camera orbit around a structure,
- sweep through trajectory frames as a smooth animation,
- show or hide tagged shapes at specific moments,
- produce a reproducible `.mp4` or `.gif` for a paper or presentation.

Use `view.export.image()` to save a static image. Use `view.player` to step
through a trajectory. See {doc}`playback`.

## Overview

| Task | Method |
|---|---|
| Add a version-1 keyframe | `view.movie.add_keyframe(time_ms, ...)` |
| Build a version-1 camera orbit | `view.movie.add_camera_orbit(duration_ms, ...)` |
| Build a version-1 trajectory sweep | `view.movie.add_structure_sweep(...)` |
| Change visibility in version 1 | `view.movie.add_visibility_transition(tag, visible, at_time_ms)` |
| Inspect timeline | `view.movie.info()` |
| Preview version 1 | `view.movie.play()` / `view.movie.stop()` |
| Preview version 2 | `await view.movie.play_async()` / `await view.movie.pause_async()` |
| Export version 1 | `view.movie.export("out.mp4", fps=25)` |
| Export version 2 | `await view.movie.export_async("out.mp4", fps=25)` |
| Save/load recipe | `view.movie.save("orbit.json")` / `view.movie.load(...)` |

The [experimental independent tracks](timeline.md#independent-tracks-experimental)
support Python evaluation of camera, structure and typed scene visibility at
arbitrary times. These recipes can travel with a saved session.

## Authoring in Studio (experimental development feature)

In a connected development view, open **Studio → Movie**. Its three tabs use
the same `view.movie` plan as Python. Apply changes in the form to update the
accepted Movie.

1. Prepare the regions, labels and interaction representations that the movie
   will use. In **Timeline**, set the duration in seconds and choose
   **Capture initial scene**.
2. Give a track a name, choose its target and property, then save a key at the
   desired time. For a camera move, capture one camera key, rotate or zoom the
   canvas, and capture another at a later time. Molecular structures use
   zero-based indices. Existing objects are addressed by their recorded names.
3. In **Preview**, choose a time and **Go to time**, or use **Play** and
   **Pause**. The slider prepares a time; it does not send repeated scene edits
   while being dragged. Restoring the initial scene requires confirmation.
4. In **Export**, enter a path in the Python session: MP4, WebM,
   lossless PNG ZIP, or an offline interactive HTML movie. Media use the chosen
   rate and pixel dimensions. A remote session writes to
   that remote filesystem. Progress and cancellation are available; the
   [export contract](export.md) describes encoders and visible-overlay limits.

Use **New track** to keep separate properties or targets independent. The
editor preserves unfinished fields when switching tabs. If Python or another
window changes the Movie meanwhile, the form is kept and applying it is
disabled: review the updated plan before choosing **Use kept draft**. An
outdated command already in transit is rejected. Replacing the plan requires
confirmation and does not silently migrate a legacy recipe. Save your session
through **Studio → Export** to preserve the plan with its molecular data.

Live actions require a compatible renderer and a running integrated async
host. Unsupported hosts show an explanation and disable those actions. The
ordinary experimental Qt host still needs that loop integration. Automated
development receiving covers actual Jupyter, canvas popups and detached Studio;
native Qt and human acceptance remain separate. The first
[offline HTML playback profile](export.md) supports static regions and live
plot/legend overlays. Development media exports can also include expanded
in-canvas plots and legends, with their supplied scientific context. The
export contract describes the layout and supported overlays.

Python and Studio share the running Movie: either can pause a preview started
by the other. Studio also shows when a capture or export was started from
Python. Cancel such an operation through its Python task; **Cancel operation**
in Studio belongs to operations started there.

## Pages

```{toctree}
:hidden:
:maxdepth: 2

timeline
playback
export
```

- {doc}`timeline` — keyframes, builders, and serialization.
- {doc}`playback` — the trajectory player (`view.player`) and the movie preview.
- {doc}`export` — video export and format options.
