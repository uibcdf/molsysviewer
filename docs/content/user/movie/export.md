(User_Movie_Export)=
# Video export

`view.movie.export()` renders each frame in the browser tick-by-tick
and stitches the PNG frames into a video file with `imageio`.

## Required dependency

```bash
pip install imageio[ffmpeg]
```

GIF output works with just `imageio`.  MP4 and WebM require the ffmpeg
plugin (`imageio[ffmpeg]`).  The dependency is checked at call time;
a clear `ImportError` is raised if it is missing.

## Basic usage

```python
# Build a timeline first
view.movie.add_camera_orbit(duration_ms=6000)

# Export to MP4 at 25 fps
path = view.movie.export("orbit.mp4", fps=25)
print(path)  # PosixPath('/path/to/orbit.mp4')
```

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `path` | — | Output file path. Format inferred from extension. |
| `fps` | 25 | Frames per second. |
| `width_px` | canvas width | Output frame width in pixels. |
| `height_px` | canvas height | Output frame height in pixels. |
| `format` | — | Explicit format override: `"mp4"`, `"gif"`, `"webm"`. |

## Supported formats

| Extension | Codec | Requirements |
|---|---|---|
| `.mp4` | H.264 via ffmpeg | `imageio[ffmpeg]` |
| `.webm` | VP9 via ffmpeg | `imageio[ffmpeg]` |
| `.gif` | Palette GIF | `imageio` (base) |

## Custom resolution

```python
view.movie.export("orbit_hd.mp4", fps=30, width_px=1920, height_px=1080)
```

## How export works

1. Python computes `total_frames = floor(duration_ms / 1000 × fps) + 1`.
2. Python sends `play_movie` with `mode="export"` to the browser.
3. JS iterates frame by frame (no wall clock):
   - Applies the interpolated state for that frame's `time_ms`.
   - Captures a PNG via the same `viewportScreenshot` helper used by
     `view.export.image()` (guaranteed complete WebGL render).
   - Emits a `movie_frame` event with the PNG as a base64 data URI.
4. Python decodes each frame and builds a list of numpy arrays.
5. On `movie_export_done`, Python calls `imageio.mimwrite()` and returns
   the resolved file path.

This is a **blocking** call.  Python polls for completion at 50 ms intervals.
A default timeout of `max(60, duration_ms/1000 × 10 + 30)` seconds applies;
pass `timeout_s=...` to override.

## GIF example

```python
view.movie.clear()
view.movie.add_camera_orbit(duration_ms=3000, n_keyframes=18)
view.movie.export("orbit_loop.gif", fps=15)
```

GIF files are larger than MP4 for the same quality.  Use a lower fps
and fewer keyframes for small file sizes.

## Saving a recipe and exporting later

```python
view.movie.save("recipes/orbit.json")

# On a different view or session:
view2.movie.load("recipes/orbit.json")
view2.movie.export("orbit.mp4")
```

## Notes

- The export is rendered in the **live Jupyter browser canvas**.
  The viewer must be visible (in an open notebook output cell) for the
  export to succeed.
- For a headless (server-side) export workflow, see the standalone host
  direction in the developer guide (`devguide/standalone_direction.md`).
