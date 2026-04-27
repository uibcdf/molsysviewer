(User_Movie_Playback)=
# Browser playback

`view.movie.play()` sends the timeline to the browser and starts a
smooth `requestAnimationFrame`-driven animation.

## Basic usage

```python
view.movie.add_keyframe(0, camera=view.camera.get_snapshot())
view.movie.add_camera_orbit(duration_ms=5000)

view.movie.play()
```

The animation runs in the embedded Mol* canvas.  You can interact
with the viewer while it plays (zoom, rotate) but the movie will
override the camera each frame.

## Stopping playback

```python
view.movie.stop()
```

## Looping

```python
view.movie.play(loop=True)
# Runs indefinitely; call view.movie.stop() to end.
```

## What the browser does

When `play()` is called:

1. Python sends the keyframe list to JS as a single `play_movie` message.
2. JS starts a `requestAnimationFrame` loop using wall-clock time.
3. Each tick interpolates between the two keyframes that enclose the
   current time and applies the result to the scene.
4. When the animation ends (non-loop), JS emits a `movie_playback_done`
   event back to Python.

Interpolation rules:

| Field | Method |
|---|---|
| `camera.position`, `camera.target` | Linear interpolation |
| `camera.up` | `normalize(lerp(a, b, t))` — stays a unit vector |
| `structure_index` | `round(lerp(a, b, t))` — integer steps |
| `layer_visibility` | Step change at the keyframe boundary |

## Notes

- `play()` does **not** block Python.  The animation runs asynchronously
  in the browser.
- `play_movie` and `stop_movie` are not recorded in the message history and
  are not replayed in HTML exports or popup sync.
- At least two keyframes are required; `play()` raises `ValueError` otherwise.
