(User_Movie_Playback)=
# Browser playback

Two different things play in a viewer, and they are worth telling apart before you reach
for either.

**`view.player`** steps through the structures of a trajectory: frame 0, frame 1, frame 2.
It is the transport control, and it is what the play button in the viewer's own UI drives.

**`view.movie`** plays a *timeline you authored* — camera moves, visibility changes, a
sweep through frames — interpolated between keyframes. It is a story about the scene, not
a way to look through it.

This page covers both, the trajectory player first.

## Playing a trajectory

```python
import molsysviewer as msv

view = msv.demo["pentalanine"]
view.player.n_structures      # 5000
view.player.play()
view.player.pause()
```

`play()` takes the settings you would otherwise set one at a time, and applies them for
this run:

```python
view.player.play(fps=15, mode="ping-pong", direction="backward", step_size=10)
```

| argument | accepts | means |
| --- | --- | --- |
| `fps` | an integer | frames drawn per second |
| `mode` | `"loop"`, `"once"`, `"ping-pong"` | what happens at the end |
| `direction` | `"forward"`, `"backward"` | which way it runs |
| `step_size` | an integer | render every *n*-th frame |

Each has a setter of its own — `set_fps`, `set_mode`, `set_direction`, `set_step_size` —
for changing one while the rest stand.

`step_size` is the one to reach for on a long trajectory: rendering every tenth frame is
ten times less work and usually looks the same. {doc}`../troubleshooting/performance` says
more about when that matters.

## Moving frame by frame

```python
view.player.go_to_structure(5)   # index -> 5
view.player.step_forward(3)      # index -> 8
view.player.step_backward()      # index -> 7
view.player.go_to_last()         # index -> 4999
view.player.go_to_first()        # index -> 0
```

`index`, `n_structures`, `is_playing`, `fps`, `mode`, `direction` and `step_size` are
readable at any time, so a script can ask where the viewer is rather than assume:

```python
if not view.player.is_playing:
    view.player.go_to_structure(view.player.n_structures // 2)
```

## Playing an authored movie

`view.movie.play()` sends the timeline to the browser and starts a
smooth `requestAnimationFrame`-driven animation.

### Basic usage

```python
view.movie.add_keyframe(0, camera=view.camera.get_snapshot())
view.movie.add_camera_orbit(duration_ms=5000)

view.movie.play()
```

The animation runs in the embedded Mol* canvas.  You can interact
with the viewer while it plays (zoom, rotate) but the movie will
override the camera each frame.

### Stopping playback

```python
view.movie.stop()
```

### Looping

```python
view.movie.play(loop=True)
# Runs indefinitely; call view.movie.stop() to end.
```

### What the browser does

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

### Notes

- `play()` does **not** block Python.  The animation runs asynchronously
  in the browser.
- `play_movie` and `stop_movie` are not recorded in the message history and
  are not replayed in HTML exports or popup sync.
- At least two keyframes are required; `play()` raises `ValueError` otherwise.
