# HTML export

`view.export.html(...)` writes the current viewer state to a self-contained or
lightweight HTML file. The exported file contains a snapshot of the scene that
a browser can open without a running Python kernel.

## Quick start

```python
from molsysviewer import demo

view = demo["1TCD"]
view.styles.apply(tag="polymer-and-ligand")

# Self-contained file — open in any browser
view.export.html("scene.html")
```

## Modes

Two modes are available:

| Mode | File size | Best for |
|---|---|---|
| `"standalone"` (default) | larger | standalone sharing, desktop browsers |
| `"lite"` | smaller | docs embeds, web publication |

### `mode="standalone"`

Produces a fully self-contained HTML using the ipywidget embed machinery. All
assets are bundled inline — the file can be opened offline.

```python
view.export.html("report.html", mode="standalone")
```

### `mode="lite"`

Produces a lighter HTML that loads the viewer runtime from the CDN and replays
the message history. Suitable for embedding in documentation or sharing via a
web URL.

```python
view.export.html("docs-embed.html", mode="lite")
```

## API reference

```python
view.export.html(
    output_filename,           # path to write
    title="MolSysViewer",      # HTML <title> tag
    include_controls=True,     # on-canvas control buttons
    include_popout=True,       # popout-window button
    mode="standalone",         # "standalone" or "lite"
    inline_messages=True,      # lite only: embed messages inline vs external JSON
)
```

### `include_controls`

Set to `False` for a minimal canvas without the reset / fullscreen / background
buttons, for example when embedding inside another application that provides its
own UI:

```python
view.export.html("minimal.html", include_controls=False, include_popout=False)
```

## Reproducing the scene

The exported HTML replays all scene-building messages in order: loads, region
creations, shape overlays, visibility changes. The final scene always matches
what was in the viewer at export time, regardless of the order the Python calls
were made.

This means you can build a complex scene over many notebook cells and export it
at any point — the replay will reconstruct the scene from scratch.

## Other export formats

- **PNG image**: `view.export.image("scene.png")` — uses the browser renderer.
- **Publication figure**: `view.export.figure("fig.png")` — stronger defaults
  for print.
- **Movie (GIF/MP4)**: `view.movie.export("movie.gif")` — for trajectory animation.
- **State (JSON)**: `view.export_state()` — machine-readable scene snapshot for
  programmatic replay.

## See also

- {doc}`sphinx_html_embedding` — embedding exported HTML in Sphinx/RTD docs.
- {doc}`../movie/export` — exporting trajectory animations.
