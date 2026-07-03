# Standalone surfaces and the Qt live model

MolSysViewer renders the same viewer bundle through **four distinct surfaces**.
They differ in *transport* (how Python and the JS runtime exchange messages) and
in *lifecycle*. Do not conflate them — especially, do not use the exported HTML
as the internal mechanism of the Qt app.

## The four surfaces

| Surface | Transport (Python → JS / JS → Python) | Runtime lifecycle |
|---------|----------------------------------------|-------------------|
| **AnyWidget / Jupyter** | `widget.send(...)` / `model.on("msg:custom")` + `model.send(...)` | Persistent widget; the `MolSysView` is the backend and receives all events via `_handle_frontend_event`. |
| **Qt live shell** (`standalone_qt0`) | `page.runJavaScript(...)` via `QtMessageBridge` / `molsysviewer://` event scheme intercepted in `acceptNavigationRequest`; large payloads over `molsysviewer-payload://` | Persistent shell loaded **once**; scene updated by live messages. |
| **Exported HTML** (`build_standalone0_html`) | Initial messages embedded in a self-contained document | A portable, reproducible artifact — **not** a live channel. |
| **Docs / static views** | Same embedded-message document, generated for docs | Static snapshot. |

Key rule: the **Qt shell is a live app**, the **exported HTML is an output
format**. The Qt shell must never be driven by regenerating HTML and reloading
`QWebEngineView`; that destroys the Chromium/Mol\*/WebGL runtime on every load.
`_rebuild_qt_html` exists only for the export action.

## The Qt live-message model

- The shell HTML is loaded once (`create_standalone_qt0_window` → `setUrl`).
- The frontend initializes and emits `ready` over the event scheme.
- `QtMessageBridge` (runtime-only) queues messages with ids, a rebuild
  `generation`, ack/error/`structure_ready`/`render_ready`, per-op timeouts,
  coalescing and retry — so no message is silently dropped and stale-generation
  acks are ignored.
- A load runs `clear_all` + the reproducible scene messages under a new
  generation; the shell and its WebGL context stay alive.
- `_message_history` remains the single reproducible source of truth; ids,
  generations, acks and timeouts are runtime-only and never recorded.

See `devguide/pending_proposals/` for the design proposal and the interactive
backend follow-up.

## UI state across loads (per-generation policy)

Each load bumps the bridge `generation` and sends `clear_all` before the new
scene. The reset boundary is:

- **Preserved** (generic, shell-level, structure-independent): the window and its
  size, the menu bar, the status bar, and any purely-visual chrome. These live
  for the whole app session because the Qt shell is persistent.
- **Reset per generation** (structure-dependent scene state): layers, regions,
  shapes, measurements, and the scene "look" (background, legend, focus-fade,
  clip planes, …). `clear_all` wipes them; the load then replays exactly the
  reproducible scene of the new system.

Rationale: state that only makes sense relative to the *previous* structure must
not survive a load (a region or shape indexed into the old atoms would be wrong),
while generic shell state has no dependency on the structure and should persist
for a smooth desktop experience. Implementation:
`_build_qt_live_messages` returns `[clear_all, *export_messages]` and
`_send_viewer_messages(..., new_generation=True)` advances the generation.
