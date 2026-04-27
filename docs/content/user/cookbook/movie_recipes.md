(User_Cookbook_Movie_Recipes)=
# Movie recipes

Three patterns for `view.movie` — orbit, trajectory sweep, and storyboard —
and how to combine them.

Install the optional dependency first:

```bash
pip install imageio[ffmpeg]
```

---

## Recipe 1 — Camera orbit

Rotate the camera 360° around the current view center and export to MP4.

```python
import molsysviewer as mv

view = mv.demo["tctim"]
view

# (interact to position the camera where you want the orbit to start)

view.movie.clear()
view.movie.add_camera_orbit(
    duration_ms=6000,   # 6-second orbit
    n_turns=1,
    n_keyframes=36,     # one keyframe per 10°
    easing="linear",
)

# Preview in browser
view.movie.play()

# Export
view.movie.export("tctim_orbit.mp4", fps=25)
```

**Tips:**

- `n_keyframes=36` (one per 10°) gives a smooth result at 25 fps.
- For a slower, more cinematic feel: increase `duration_ms` and keep `n_keyframes`.
- Save the recipe so you can re-use it on other systems:

```python
view.movie.save("recipes/orbit_360.json")

# Later on view2:
view2.movie.load("recipes/orbit_360.json")
view2.movie.export("system2_orbit.mp4", fps=25)
```

---

## Recipe 2 — Trajectory sweep

Step through all trajectory frames while the camera holds still.

```python
import molsysviewer as mv

view = mv.demo["dialanine"]
view

view.movie.clear()
view.movie.add_structure_sweep(
    from_index=0,
    to_index=view.player.n_structures - 1,
    duration_ms=10_000,   # 10 seconds for the full trajectory
)

view.movie.play()
view.movie.export("dialanine_sweep.mp4", fps=25)
```

**Tips:**

- For very long trajectories, reduce `fps` or select a shorter `from_index`→`to_index` range.
- Add a camera keyframe at the start to lock the view before the sweep:

```python
view.movie.clear()
view.movie.add_keyframe(0, camera=view.camera.get_snapshot())
view.movie.add_structure_sweep(duration_ms=10_000)
```

---

## Recipe 3 — Visibility storyboard

Reveal regions one by one with step transitions at precise times.

```python
import molsysviewer as mv

view = mv.demo["tctim"]

# Set up two named regions (assumes regions already exist or created here)
# view.add_region("active-site", ...)
# view.add_region("binding-loop", ...)

snap_overview = view.camera.get_snapshot()
snap_zoom = {"position": [5, 0, 0], "target": [0, 0, 0], "up": [0, 1, 0]}

view.movie.clear()

# t=0: overview, both regions hidden
view.movie.add_keyframe(0, camera=snap_overview)
view.movie.add_visibility_transition("active-site",  visible=False, at_time_ms=0)
view.movie.add_visibility_transition("binding-loop", visible=False, at_time_ms=0)

# t=1 500 ms: show active site
view.movie.add_visibility_transition("active-site", visible=True, at_time_ms=1500)

# t=3 000 ms: zoom in with ease-in-out
view.movie.add_keyframe(3000, camera=snap_zoom, easing="ease-in-out")

# t=5 000 ms: show binding loop
view.movie.add_visibility_transition("binding-loop", visible=True, at_time_ms=5000)

# t=7 000 ms: end frame
view.movie.add_keyframe(7000)

view.movie.play()
view.movie.export("storyboard.mp4", fps=25)
```

---

## Recipe 4 — Combined orbit + sweep

Orbit the camera for 5 seconds, then sweep through trajectory frames for 5 seconds.

```python
import molsysviewer as mv

view = mv.demo["dialanine"]
view

view.movie.clear()

# Phase 1: orbit (0 → 5 000 ms)
view.movie.add_camera_orbit(duration_ms=5000, n_turns=1)

# Phase 2: trajectory sweep (5 000 → 10 000 ms, appends automatically)
view.movie.add_structure_sweep(duration_ms=5000)

view.movie.info()
# {'n_keyframes': ..., 'duration_ms': 10000.0,
#  'has_camera': True, 'has_structure_sweep': True, ...}

view.movie.export("orbit_then_sweep.mp4", fps=25)
```

---

## GIF variant

For a short, looping GIF (e.g., for a README or poster):

```python
view.movie.clear()
view.movie.add_camera_orbit(duration_ms=3000, n_turns=1, n_keyframes=18)
view.movie.export("orbit_loop.gif", fps=12)

# Preview the loop in browser
view.movie.play(loop=True)
view.movie.stop()  # when done
```
