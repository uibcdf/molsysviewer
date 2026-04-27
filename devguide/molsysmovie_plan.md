# MolSysMovie — Implementation Plan (Pre-1.0)

> **Status:** Pre-1.0. This document supersedes the strategic vision in
> `molsysmovie_vision.md` with a concrete architecture and phased plan.

## Decision Record

The original vision proposed a top-level `MolSysMovie` class separate from
`MolSysView`. After design review, the adopted direction is:

- **`view.movie`** as a `MovieManager` — consistent with `view.camera`,
  `view.player`, `view.shapes`, `view.export`, and the rest of the manager
  pattern already in the codebase.
- A movie is always about the content of a specific view (its camera, regions,
  structures). A standalone class would duplicate that coupling without benefit.
- Serialization is orthogonal: the **timeline** (keyframe list) is pure data
  and can be saved/loaded independently of the view. `view.movie.save()` /
  `view.movie.load()` let a timeline be defined once and replayed on any
  compatible view.

---

## Architecture

### Two-layer design

```
MovieManager (view.movie)
├── Runtime layer  — tied to view: play(), export(), access to
│                    view.camera, view.player, view._layers
└── Timeline layer — pure data: list of Keyframe dicts, JSON-serializable
                     save(), load(), to_dict(), from_dict()
```

### Execution model

Python defines the scientific intent; JS drives the actual animation.

```
Python                          JS MovieHandlers
──────                          ─────────────────
view.movie.add_keyframe(...)
view.movie.play()          ──►  play_movie message
                                requestAnimationFrame loop
                                  interpolate(keyframes, t)
                                  → camera.setState()
                                  → set_structure op
                                  → show/hide layer ops

view.movie.export(path)    ──►  play_movie message (mode=export)
                                tick-by-tick (no wall clock)
                                  apply state
                                  wait one render tick
                                  capture PNG (same path as export.image)
                                  send movie_frame event  ──►  Python
                                                               collects frames
                                                               stitches with
                                                               imageio/ffmpeg
```

This is the same separation as `view.export.image()` (Python orchestrates,
JS captures) but extended to a frame sequence.

---

## Data Model

### Keyframe

A keyframe is a plain dict — all fields optional except `time_ms`:

```python
{
    "time_ms": 3000,
    "camera": {
        "position": [x, y, z],   # Å (same convention as camera snapshots)
        "target":   [x, y, z],   # Å
        "up":       [x, y, z],
    },
    "structure_index": 24,        # int; None means "keep current"
    "layer_visibility": {         # tag → bool; missing tags are unchanged
        "active-site": True,
        "solvent":      False,
    },
    "easing": "ease-in-out",      # per-segment, applies to interval
                                  # [this_keyframe, next_keyframe]
}
```

Supported easing values: `"linear"`, `"ease-in"`, `"ease-out"`,
`"ease-in-out"`.

### Timeline

The timeline is the ordered list of keyframes. Invariants:
- `time_ms` values are strictly increasing.
- At least two keyframes required for any animation.
- Gaps (time between last keyframe and end) hold the last state.

### Serialized form

`view.movie.to_dict()` returns:

```json
{
  "molsysmovie_version": 1,
  "keyframes": [ ... ],
  "metadata": {
    "created_by": "molsysviewer",
    "n_structures": 100
  }
}
```

---

## Python API

### Core methods

```python
# Timeline construction
view.movie.clear()
view.movie.add_keyframe(
    time_ms,
    *,
    camera=None,           # dict snapshot or None (keep current)
    structure_index=None,  # int or None
    layer_visibility=None, # {tag: bool} or None
    easing="linear",
)

# Convenience builders (generate multiple keyframes internally)
view.movie.add_camera_orbit(
    duration_ms=5000,
    n_turns=1,
    start_time_ms=0,       # offset into timeline
    center=None,           # defaults to current camera target
    elevation=None,        # radians; defaults to current camera elevation
    easing="linear",
)
view.movie.add_structure_sweep(
    from_index=0,
    to_index=None,         # defaults to player.n_structures - 1
    start_time_ms=0,
    duration_ms=None,      # required if end_time_ms not given
    end_time_ms=None,
)
view.movie.add_visibility_transition(
    tag,
    visible,               # bool
    at_time_ms,
)

# Inspection
view.movie.info()          # returns timeline summary (n keyframes, duration)
view.movie.duration_ms     # property: time_ms of last keyframe

# Browser playback
view.movie.play(loop=False)
view.movie.stop()

# Export
view.movie.export(
    path,                  # .mp4 / .gif / .webm; format inferred from extension
    *,
    fps=25,
    width_px=None,         # defaults to current canvas width
    height_px=None,
    format=None,           # explicit override ("mp4", "gif", "webm")
)

# Serialization
view.movie.to_dict()       # pure data dict
view.movie.from_dict(data) # replaces current timeline
view.movie.save(path)      # writes JSON
view.movie.load(path)      # reads JSON, replaces timeline
```

### Usage examples

**Orbit:**
```python
view.movie.clear()
view.movie.add_keyframe(time_ms=0, camera=view.camera.get_snapshot())
view.movie.add_camera_orbit(duration_ms=6000, n_turns=1)
view.movie.play()
view.movie.export("orbit.mp4", fps=30)
```

**Trajectory sweep with camera path:**
```python
view.movie.clear()
view.movie.add_keyframe(
    time_ms=0,
    camera=view.camera.get_snapshot(),
    structure_index=0,
)
view.movie.add_structure_sweep(from_index=0, to_index=99, duration_ms=10_000)
view.movie.add_keyframe(
    time_ms=10_000,
    camera={"position": [...], "target": [...], "up": [...]},
    structure_index=99,
)
view.movie.export("trajectory.mp4", fps=25)
```

**Storyboard with visibility transitions:**
```python
view.movie.clear()
view.movie.add_keyframe(time_ms=0, camera=snap_overview)
view.movie.add_visibility_transition("active-site", visible=True,  at_time_ms=1000)
view.movie.add_keyframe(time_ms=3000, camera=snap_zoom_pocket, easing="ease-in-out")
view.movie.add_visibility_transition("active-site", visible=False, at_time_ms=5000)
view.movie.export("storyboard.mp4", fps=25)
```

**Serializable recipe:**
```python
# Define once
view.movie.add_camera_orbit(duration_ms=5000)
view.movie.save("recipes/orbit_360.json")

# Apply on any compatible view
view2.movie.load("recipes/orbit_360.json")
view2.movie.export("view2_orbit.mp4")
```

---

## JS Architecture

### New file: `src/managers/handlers/movie-handlers.ts`

```typescript
interface Keyframe {
  time_ms: number;
  camera?: CameraSnapshot;
  structure_index?: number;
  layer_visibility?: Record<string, boolean>;
  easing: EasingName;
}

interface PlayMovieMessage {
  op: "play_movie";
  keyframes: Keyframe[];
  loop: boolean;
  mode: "play" | "export";
  fps?: number;      // export mode only
  width_px?: number;
  height_px?: number;
}
```

#### Play mode

- Uses `requestAnimationFrame` loop with wall-clock `performance.now()`.
- At each tick: computes `t = (now - start) / duration`, finds the active
  segment, applies easing, interpolates all state fields.
- Camera: `lerp(posA, posB, t)` for position and target; `normalize(lerp(upA, upB, t))`
  for up vector; applies via `canvas3d.camera.setState(snapshot, 0)` (instant, since
  JS is already driving the interpolation tick by tick).
- Structure index: `Math.round(lerp(a, b, t))` — emits `set_structure` only on
  change.
- Layer visibility: step at the keyframe boundary time (no cross-fade in v1).
- On loop end: emits `{ event: "movie_playback_done" }` to Python (unless
  `loop: true`).

#### Export mode

- No wall-clock. Iterates `frame_index` from 0 to `totalFrames - 1`.
- Per frame:
  1. Compute `time_ms = frame_index / fps * 1000`.
  2. Apply interpolated state (same logic as play mode).
  3. `await renderFrame()` — uses the same screenshot helper as
     `buildImageExportPayload` to guarantee a completed WebGL render.
  4. Emit `{ event: "movie_frame", frame_index, total_frames, data_uri }`.
- On completion: emit `{ event: "movie_export_done", total_frames }`.
- Progress events allow Python to show a progress bar.

### Message additions (`viewer-messages.ts`)

```typescript
// Python → JS
PlayMovieMessage
StopMovieMessage

// JS → Python (frontend events)
MovieFrameEvent        // one per frame in export mode
MovieExportDoneEvent   // end of export
MoviePlaybackDoneEvent // end of browser playback (non-loop)
```

---

## Python Export Pipeline

```
view.movie.export("out.mp4", fps=25)
  │
  ├─ validate timeline (≥ 2 keyframes)
  ├─ compute total_frames = ceil(duration_ms / 1000 * fps)
  ├─ send play_movie (mode="export", fps=25, ...)
  │
  │   JS emits movie_frame events one by one
  │
  ├─ collect frames into list[bytes] (decode base64 data_uri)
  ├─ on movie_export_done:
  │   ├─ imageio.mimwrite(path, frames, fps=fps)   # GIF / MP4 / WebM
  │   └─ or subprocess ffmpeg if imageio unavailable
  └─ return path
```

Optional dependency: `imageio[ffmpeg]`. MolSysViewer should check at
call time and raise a clear `ImportError` if missing, not at import time.

---

## Interpolation Reference

| Field | Method | Notes |
|---|---|---|
| `camera.position` | `lerp(a, b, t_eased)` | component-wise |
| `camera.target` | `lerp(a, b, t_eased)` | component-wise |
| `camera.up` | `normalize(lerp(a, b, t_eased))` | stays unit vector |
| `structure_index` | `Math.round(lerp(a, b, t_eased))` | int step |
| `layer_visibility` | step at keyframe boundary | no cross-fade in v1 |

Easing functions (standard cubic Bézier control points):

| Name | P1 | P2 |
|---|---|---|
| `linear` | 0.0, 0.0 | 1.0, 1.0 |
| `ease-in` | 0.42, 0.0 | 1.0, 1.0 |
| `ease-out` | 0.0, 0.0 | 0.58, 1.0 |
| `ease-in-out` | 0.42, 0.0 | 0.58, 1.0 |

---

## `add_camera_orbit` geometry

Given the current camera snapshot (`position`, `target`, `up`):

1. Compute `radius = |position - target|`.
2. Compute `radial = (position - target) / radius` — unit vector from target
   to camera.
3. Compute `right = cross(radial, up)` (normalized).
4. For each keyframe `i` in `[0, n_keyframes]`:
   - `θ = 2π * n_turns * i / n_keyframes`
   - `new_radial = cos(θ) * radial + sin(θ) * right`
   - `new_position = target + radius * new_radial`
   - keyframe camera: `{position: new_position, target: target, up: up}`

This keeps the camera at constant distance and elevation, rotating in the
plane defined by `radial` and `right`. The final keyframe closes the loop
(same as the first).

---

## Phased Implementation Plan

### Phase 1 — Python data model

- `molsysviewer/viewer/movie.py` — `MovieManager` class
- `Keyframe` dataclass (or typed dict)
- `add_keyframe()`, `add_visibility_transition()`
- `clear()`, `info()`, `duration_ms`
- `to_dict()`, `from_dict()`, `save()`, `load()`
- Unit tests (no JS required): timeline construction, serialization,
  ordering invariants, round-trip save/load
- Wire `view.movie` in `viewer/core.py`

### Phase 2 — JS animation engine (browser play)

- `movie-handlers.ts` with play mode only
- `play_movie` / `stop_movie` message types
- Interpolation: camera lerp, structure index step, easing
- `view.movie.play()` / `stop()` in Python
- `MoviePlaybackDoneEvent` back to Python
- JS unit tests: interpolation math, keyframe segment lookup, easing

### Phase 3 — Export pipeline

- Export mode in `movie-handlers.ts`: tick-by-tick, `renderFrame()`,
  `movie_frame` events
- Python: frame collection, imageio stitching
- `view.movie.export(path, fps, width_px, height_px)`
- Test: export a 3-keyframe, 3-frame movie in a headless test and verify
  frame count

### Phase 4 — Convenience builders

- `add_camera_orbit()` — geometry as documented above
- `add_structure_sweep()` — populates keyframes for structure_index range
- Unit tests for each builder's generated keyframe sequences

### Phase 5 — Docs and devguide closure

- User-facing docs: `docs/content/user/movie/index.md`
- Cookbook recipe: orbit + trajectory sweep + storyboard
- Update `molsysmovie_vision.md` header to point here
- Update `roadmap.md` to mark `view.movie` as planned/in-progress
- Update `checkpoints.md`

---

## Integration Points With Existing Systems

| System | How movie uses it |
|---|---|
| `view.camera` | `get_snapshot()` to seed keyframes; same dict format |
| `view.player` | `n_structures` for sweep bounds; existing `set_structure` op reused |
| `view.export.image()` | Export mode reuses the same `renderFrame` JS helper |
| `view._layers` / regions | Tag validation in `add_visibility_transition()` |
| `view._message_history` | Movie play/export ops are NOT recorded in history (runtime-only, not replay artifacts) |

---

## Constraints

- Movie ops are **not** added to `_message_history`. A movie is a runtime
  action, not a reproducible scene state op. HTML export and popup sync
  must not attempt to replay movie playback.
- The JS animation loop must not interfere with Mol*'s own interaction
  trackball. `play_movie` should disable trackball during playback and
  restore it on stop/done.
- Frame capture in export mode must use the same screenshotting path as
  `export.image()` to guarantee a completed WebGL render (not a raw
  `canvas.toDataURL()` which may catch a partial frame).
- `imageio[ffmpeg]` is an optional dependency. Check at call time.

---

## Open Questions (Phase 2+)

- Should `play()` support a `start_time_ms` offset to preview from mid-timeline?
- Should `layer_visibility` transitions support a `fade_duration_ms` for
  smooth opacity cross-fade (requires per-layer opacity interpolation in JS)?
- Should the camera orbit helper support non-horizontal orbits
  (arbitrary axis)?
- Should `export()` support a progress callback for notebook use
  (`tqdm`-style)?
- Should the serialized format be versioned and validated against a schema?
- Should a future `MovieRecipe` top-level object (view-independent) wrap
  the serialized timeline for sharing across views more explicitly?
