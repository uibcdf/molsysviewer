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
- tell a visual story by showing/hiding regions at specific moments,
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
| Save/load recipe | `view.movie.save("orbit.json")` / `view.movie.load(...)` |

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
