# Architecture

- **Python layer**: `MolSysView`, loaders, and shape APIs send JSON-like messages to the frontend.
- **Frontend**: AnyWidget entry `js/src/index.ts` initializes Mol*, routes messages in `managers/viewer-controller.ts`, and builds shapes in `shapes/`.
- **Shapes & tags**: shape builders register Mol* state refs; tags allow selective clearing.
- **Data flow**: Python → message → JS controller → Mol* state tree → renderer; visibility uses transparency over atom masks.
- **Generated artifacts**: `viewer.js`/`.map` are produced from `js/src/` with esbuild; never edit them directly.
- **Doc embeds**: prefer `view.export.html(..., mode="lite")` to export docs-light views and `molsysviewer.thirds.jupyter.load_html_in_notebook` to embed them in docs notebooks. `MolSysView.write_html(...)` remains as a deprecated compatibility alias.
- For a detailed architecture reference, see {doc}`architecture_full`.

Developer-facing structure
- `molsysviewer/viewer.py`: message queue, visibility masks, shape manager, exports.
- `molsysviewer/shapes/`: Python APIs; normalize inputs and send ops.
- `molsysviewer/js/src/`: Mol* plugin init, message routing, geometry builders (organized into managers/, shapes/, plugin/, messages/, index.ts).
- `docs/`: Sphinx site (pydata theme, MyST, notebooks off), static views under `_static/views/`.

Message flow (conceptual)
- Python API call → `_send` builds a JSON-like message with `op` + `options`.
- JS controller (`viewer-controller.ts`) handles the `op`, validates options, and calls `add*FromPython` helpers.
- Mol* state tree is updated; refs are tracked per tag for selective clear.
- Visibility updates are applied via transparency (hidden atoms become fully transparent).

WebGL boundary
- MolSysViewer does not draw directly; Mol* owns WebGL. We prepare geometry/state; Mol* renders.
- AnyWidget hosts the canvas; the Mol* plugin attaches to it and manages lifecycle.
