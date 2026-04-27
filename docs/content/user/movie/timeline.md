(User_Movie_Timeline)=
# Timeline and keyframes

The timeline is an ordered list of keyframes.  Each keyframe says
*what the scene should look like* at a given time.

## Keyframe fields

Every keyframe has a `time_ms` timestamp (milliseconds).
All other fields are optional — missing fields mean "keep the current value".

| Field | Type | Effect |
|---|---|---|
| `time_ms` | `float` | Timestamp in milliseconds (**required**). |
| `camera` | `dict` | `{position, target, up}` in Å. |
| `structure_index` | `int` | Trajectory frame to show. |
| `layer_visibility` | `dict[str, bool]` | Step-change visibility per tag. |
| `easing` | `str` | Transition curve to the *next* keyframe. |

Easing values: `"linear"` (default), `"ease-in"`, `"ease-out"`, `"ease-in-out"`.

## Adding keyframes manually

```python
import molsysviewer as mv

view = mv.demo["dialanine"]

# Capture the current camera
snap = view.camera.get_snapshot()

# Start at t=0 and end at t=5 000 ms
view.movie.add_keyframe(0, camera=snap)
view.movie.add_keyframe(5000, camera={"position": [15, 0, 0],
                                       "target":   [0, 0, 0],
                                       "up":       [0, 1, 0]})

view.movie.info()
# {'n_keyframes': 2, 'duration_ms': 5000.0, 'has_camera': True, ...}
```

Rules:

- `time_ms` values must be **strictly increasing**.
- At least **two keyframes** are required before `play()` or `export()`.

## Camera orbit builder

`add_camera_orbit` generates a full 360° orbit in one call.

```python
view.movie.clear()
view.movie.add_camera_orbit(duration_ms=6000, n_turns=1, n_keyframes=36)
# 37 keyframes (36 steps + closing frame), t=0→6 000 ms
```

Key parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `duration_ms` | 5000 | Total orbit duration. |
| `n_turns` | 1.0 | Number of full rotations. |
| `n_keyframes` | 36 | Keyframes per turn (higher = smoother). |
| `center` | camera target | Orbit center in Å. |
| `easing` | `"linear"` | Easing for each inter-keyframe segment. |

The geometry is computed from the **current camera snapshot** at call time.
Position, target, and up are taken from `view.camera.get_snapshot()`.

## Trajectory sweep builder

`add_structure_sweep` steps through trajectory frames.

```python
view.movie.clear()
view.movie.add_structure_sweep(
    from_index=0,
    to_index=99,
    duration_ms=10_000,
)
# 100 keyframes, each with structure_index 0..99
```

Key parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `from_index` | 0 | First structure index. |
| `to_index` | `n_structures - 1` | Last structure index (inclusive). |
| `duration_ms` | — | Sweep duration (provide this **or** `end_time_ms`). |
| `end_time_ms` | — | Absolute end time (alternative to `duration_ms`). |
| `start_time_ms` | `duration_ms` of last keyframe | When to start. |

## Visibility transitions

`add_visibility_transition` inserts a step-change in layer visibility.

```python
view.movie.add_keyframe(0)
view.movie.add_keyframe(6000)

view.movie.add_visibility_transition("active-site", visible=True,  at_time_ms=1000)
view.movie.add_visibility_transition("active-site", visible=False, at_time_ms=5000)
```

If a keyframe already exists at `at_time_ms`, the entry is merged into it.
Otherwise a new keyframe is inserted at the correct sorted position.

## Chaining builders

Builders always append *after* the last existing keyframe by default.
You can chain them to produce a compound animation:

```python
view.movie.clear()

# First 6 s: camera orbit
view.movie.add_camera_orbit(duration_ms=6000)

# Next 4 s: trajectory sweep (starts at t=6 000 ms automatically)
view.movie.add_structure_sweep(duration_ms=4000)

view.movie.duration_ms  # 10 000.0
```

## Timeline inspection

```python
info = view.movie.info()
# {
#   'n_keyframes': 137,
#   'duration_ms': 10000.0,
#   'has_camera': True,
#   'has_structure_sweep': True,
#   'has_visibility_transitions': False,
# }

view.movie.duration_ms  # 10000.0
view.movie.keyframes    # list of dicts (read-only snapshot)
```

## Serialization

The timeline is pure data and can be saved to JSON and replayed on any view.

```python
# Save
view.movie.save("recipes/orbit_360.json")

# Load on a different view
view2.movie.load("recipes/orbit_360.json")
view2.movie.play()
```

`to_dict()` / `from_dict()` work with plain Python dicts:

```python
data = view.movie.to_dict()
# {'molsysmovie_version': 1, 'keyframes': [...]}

view2.movie.from_dict(data)
```

## Clearing the timeline

```python
view.movie.clear()
view.movie.duration_ms  # 0.0
```
