# MolSysViewer Concepts (Python ↔ AnyWidget ↔ Mol* ↔ WebGL)

## Layers and roles
- **Python layer (`MolSysView`)**: user-facing API, message queue, loaders, shape managers. It owns selections/masks and sends JSON-like messages to the frontend.
- **AnyWidget/ipywidgets**: bridges Python to the browser. The generated bundle (`molsysviewer/viewer.js`) runs inside the notebook frontend; Python sends messages, JS responds.
- **Mol\***: rendering engine inside the JS bundle. It builds meshes, manages state, and talks to WebGL. We reuse Mol\* internals (representations, mesh builders, themes) rather than reimplementing rendering.
- **WebGL**: the GPU-backed rendering context Mol\* uses to draw. MolSysViewer itself does not touch WebGL directly; Mol\* does.
- **MolSysViewerController (JS)**: orchestrates Mol\* plugin init, routes messages (`op`), builds shapes, tracks refs/tags, and cleans up state objects.

## Message flow (Python → JS → Mol\* → WebGL)
1. Python API call (e.g., `add_pocket_blob`) normalizes inputs and sends a message: `{"op": "add_pocket_blob", "options": {...}}`.
2. AnyWidget delivers the message to the JS bundle.
3. `MolSysViewerController` handles the `op`, validates options, and calls the appropriate `add*FromPython` helper.
4. Mol\* constructs geometry/state (meshes, volumes, tubes, glyphs) and renders via WebGL.
5. Shape refs are tracked with optional `tag` for selective clearing.

## Why MolSysViewer (vs. raw Mol\*)
- **Jupyter-native**: ships a prebuilt bundle; no Node.js needed for users. AnyWidget handshake and message queue handled for you.
- **Python-first API**: simple calls (`load_*`, `add_*`) with normalized options and MolSysMT-compatible selections.
- **Domain overlays**: pocket blobs/surfaces, channel tubes, anisotropy ellipsoids/disks, pharmacophore glyphs—purpose-built for TopoMT/PharmacophoreMT workflows.
- **Tag-based management**: add/clear shapes by tag; manage overlays predictably.
- **Integration**: works with MolSysMT payloads; relies on Mol\* internals (not a black box) for correctness and performance.
- **Packaging**: bundle committed so conda/pip users get a working viewer without extra steps.

## Shape philosophy (API → Mol\* → WebGL)
- Python APIs normalize inputs (lengths, types, defaults) and produce structured options.
- Messages carry those options to JS, where geometry builders (in `js/src/shapes/`) translate them into Mol\* meshes/volumes/representations.
- Mol\* handles the actual rendering pipeline; we focus on data prep, color/alpha mapping, and lifecycle (refs/tags).

## Key components
- `MolSysView` (Python): owns widget, masks, loaders, shapes manager; exports static HTML via `write_html`.
- `MolSysViewerController` (JS): initializes Mol\*, routes messages, manages refs/tags, clears shapes/styles.
- `js/src/shapes/`: geometry helpers (spheres, pockets, blobs, tubes, ellipsoids, pharmacophore, etc.).
- `js/src/managers/` and `plugin/`: message handling and structure loading.
- Static docs embeds: export with `write_html` into `_static/views/`; embed with `molsysviewer.thirds.load_html_in_jupyter_notebook`.
