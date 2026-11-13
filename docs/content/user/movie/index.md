(User_Movie)=
# Movie

`view.movie` lets you define a keyframe timeline, preview it in the browser,
and export it to a video file — all from a Python notebook.

A movie is always about the content of a specific view: its camera, regions,
layers, and structures.  The timeline is pure data: you can save it to JSON
and replay it on any compatible view.

## When to use `view.movie`

Use `view.movie` when you need to:

- record a camera orbit around a structure,
- sweep through trajectory frames as a smooth animation,
- show or hide tagged shapes at specific moments,
- produce a reproducible `.mp4` or `.gif` for a paper or presentation.

If you just want a static image, use `view.export.image()` instead. And if all you want
is to *step through a trajectory*, that is `view.player`, not a movie — see
{doc}`playback`.

## Overview

| Task | Method |
|---|---|
| Add a keyframe | `view.movie.add_keyframe(time_ms, ...)` |
| Camera orbit | `view.movie.add_camera_orbit(duration_ms, ...)` |
| Trajectory sweep | `view.movie.add_structure_sweep(...)` |
| Visibility step | `view.movie.add_visibility_transition(tag, visible, at_time_ms)` |
| Inspect timeline | `view.movie.info()` |
| Preview in browser | `view.movie.play()` / `view.movie.stop()` |
| Export to file | `view.movie.export("out.mp4", fps=25)` |
| Export independent tracks (experimental development API) | `await view.movie.export_async("out.mp4", fps=25)` |
| Save/load recipe | `view.movie.save("orbit.json")` / `view.movie.load(...)` |

The [experimental independent tracks](timeline.md#independent-tracks-experimental)
support Python evaluation of camera, structure and typed scene visibility at
arbitrary times. These recipes can travel with a saved session.

## Authoring in Studio (experimental development feature)

In a connected development view, open **Studio → Movie**. Its three tabs use
the same `view.movie` plan as Python; changing a form alone does not change
the accepted Movie or molecular system. This editor is not available in the
public 0.24.0 package or a standalone HTML export.

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
export contract describes the layout restrictions and explicit exclusions;
these features are not in the public 0.24.0 package. Richer portable profiles
remain in development.

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
