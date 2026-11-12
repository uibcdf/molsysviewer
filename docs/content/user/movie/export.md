(User_Movie_Export)=
# Video export

## Exporting independent tracks (experimental)

The development API `await view.movie.export_async(...)` exports a version-2
Movie through a live primary canvas with `movie_frame_capture` version 1.
Published-package and native Qt qualification remain separate from source tests.
The qualified public 0.24.0 package does not offer this new method.

After preparing a live view and its
[independent tracks](timeline.md#independent-tracks-experimental), you can write:

```python
result = await view.movie.export_async(
    "movie.mp4", fps="30000/1001", width_px=1280, height_px=720,
)
print(result["path"])
print(result["manifest"]["sampling"])
```

Install the optional Movie dependencies with `pip install 'molsysviewer[movie]'`.
MP4/H.264 and WebM/VP9 use `imageio-ffmpeg>=0.6.0`; all formats use ImageIO for
PNG decoding. A missing renderer or encoder raises an error.

This implementation exports camera, structure, visibility and the
[admitted appearance tracks](timeline.md#animating-appearance).
Keep untracked scene settings unchanged after authoring; explicit baseline
reset and reviewed rebase routes are described in the timeline documentation.
The [experimental Studio editor](index.md#authoring-in-studio-experimental-development-feature)
uses the same export API. Richer style recipes and complete authoring
acceptance remain in development.

You can also export lossless images:

```python
result = await view.movie.export_async("frames.zip", format="pngs", fps=25)
```

The ZIP holds numbered PNG files and `manifest.json`. Videos carry that
manifest in their comment metadata. It records the recipe, runtime/encoder
identity, frame-rate ratio, resolution, composition and render quality.
Keep your molecular session to edit the story later.

| Argument | Default | Meaning |
| --- | --- | --- |
| `fps` | `25` | Positive frames per second, up to 240; rational strings are accepted. |
| `width_px`, `height_px` | `1280`, `720` | Exact resolution. Video dimensions must be even. |
| `sample_level` | `2` | Mol* multisampling level, from 0 to 5; the interactive canvas keeps its settings. |
| `format` | inferred | `"mp4"`, `"webm"` or `"pngs"`. |
| `overwrite` | `False` | Replace an existing output only after successful completion. |
| `include_overlays` | `True` | Require support for visible scientific overlays. |
| `timeout` | `15.0` | Renderer/encoder wait budget in seconds, up to 300. |
| `on_progress` | `None` | Synchronous callback receiving completed-frame counts and movie time in milliseconds. |

Native labels and measurements are included. Visible DOM plots and legends
currently require hiding or an explicit `include_overlays=False` exclusion.
The manifest records this choice. Authoring controls are excluded.

Samples cover `[0, duration)` at a constant rate. A one-second movie at 25 fps
contains 25 samples, ending at 960 ms. Add a final hold when you want the ending
pose to remain visible. Each image is encoded before requesting the next.
The destination is published only after successful completion. Cancel the
Python task to cancel export; an interrupted job preserves an existing file.
The view stays at its last applied pose. Use `await view.movie.seek_async(0)`
to return to the start.

## Exporting legacy keyframes (version 1)

`view.movie.export()` renders each frame in the browser tick-by-tick
and stitches the PNG frames into a video file with `imageio`.
This synchronous compatibility route retains its historical collection and
sampling behavior. Use `export_async()` for the bounded version-2 workflow.

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
| `format` | — | Validated legacy hint; the filename suffix currently selects its writer. |

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
