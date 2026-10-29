# Standalone surfaces and the Qt live model

The local browser and Qt standalone hosts are **experimental for 1.0**. Their
launchers and host APIs are outside the 1.0 support promise. Interactive HTML
export remains a supported output format. Remote sessions are an unsupported
preview whose supported workflow is planned after 1.0.

The core public pair is qualified on Linux x86_64/ARM64, macOS Apple Silicon
and Windows x86_64 with Python 3.11–3.14. Those installed notebook/browser gates
and the Windows launcher `--help` gate do not certify Qt. The separate Qt
[development recipe](https://github.com/uibcdf/molsysviewer/blob/main/devguide/standalone_supported_environment.md)
records Linux transport observations and Windows/macOS solver-only evidence;
Linux native-window source observations now cover live replacement, exports and
independent windows. They do not certify installed artifacts, Windows/macOS,
or the standalone host for 1.0.

MolSysViewer renders the same viewer bundle through **four distinct surfaces**.
They differ in *transport* (how Python and the JS runtime exchange messages) and
in *lifecycle*. Do not conflate them — especially, do not use the exported HTML
as the internal mechanism of the Qt app.

## How each one is entered

The table below is about mechanism; these are the names you actually call.

| Surface | Entry point |
| --- | --- |
| AnyWidget / Jupyter | `msv.new_view(...)`, or `msv.demo[...]` |
| Qt live shell | `molsysviewer.launch_standalone_qt0(molecular_system, ...)`, or the `molsysviewer-qt` console script |
| Exported HTML | `molsysviewer.build_standalone0_html(...)`, and `view.export.html(...)` for the ordinary case |
| Docs / static views | the same builder, driven by the docs pipeline |

`launch_standalone_qt0` opens the window **and runs the Qt event loop**, so it does not
return until the window closes. When you need the window without surrendering the thread —
embedding it in a Qt application of your own, or driving it from a test — call
`create_standalone_qt0_window` instead, which takes the same arguments minus `exec_app` and
hands back the objects it built.

Both accept the loading arguments a view accepts (`selection`, `structure_indices`,
`syntax`, `load_mode`), the chrome switches (`include_controls`, `include_popout`,
`width`, `height`, `title`), and the add-on switches (`discover_addons`, `addon_modules`).

### Reaching the current scene from another surface

`view.build_popup_scene_snapshot(mode, endpoint=None, include_molecular=True)` returns the
list of messages a second surface must replay to arrive at the scene the view is showing
now — the popup's equivalent of what the exported HTML embeds. `mode` is the surface being
built for (`"canvas"` or `"panel"`); `include_molecular=False` omits the structure payload
when the receiver already has it.

It is a *snapshot*, not a subscription: what it returns is true at the moment it is called,
and a later change reaches the popup as an ordinary live message.

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
  coalescing and bounded retry. Once the frontend is ready, delivery failures
  are retried up to five times with backoff; exhausting that budget discards the
  message with a status-bar report and a compact runtime record. An ack timeout
  is terminal and reported but is not retried. Stale-generation acks are ignored.
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

## Live authority, preferences and exports

The local shell explicitly sets `host_event_transport="url-scheme"`. Its
controller sends product events to its persistent Python view, including shared
Studio and context-menu actions. Static HTML keeps its authority-free behavior.
The local native Reset-only context menu has been removed; the canvas uses the
shared menu. There is no second Qt-specific scene owner.

`QtViewChannel` reuses the widget's trait defaults and validators without
creating an AnyWidget or a comm. Python preferences travel through
`set_host_ui`; browser preference changes return as whitelisted `qt_ui_state`
events. These preferences are transport state, outside scene history. A load
replays them after advancing its generation. A final `commit_scene` waits for
a completed Mol* draw and presentation before the shell reports `Ready.`.

Camera and image requests use the same frontend reply handlers in Qt and
Jupyter. Synchronous Python waiting cooperatively pumps the Qt event loop;
missing replies still terminate with a timeout. Movie export waits for each
requested camera state to be drawn before capturing its image.

The native Export menu exports the **current persistent view**, including scene
edits. HTML output is self-contained through `view.export.html(...)`, without
the live Qt connector. Studio downloads use the profile's native destination
dialog; cancellation does not create a destination. Interrupted and completed
downloads have different status messages.

The shared Fullscreen API controls the native window and restores its previous
maximized/normal state. Escape belongs to the canvas first (menus, tools,
selection and panels); an unconsumed Escape exits fullscreen. A native menu
shortcut must not steal this key before WebEngine receives it.

## Local host ownership and limits

Each local host owns a private off-the-record WebEngine profile, page, scheme
handlers, payload store and Python view. Independent windows cannot overwrite
each other's transport handlers. Closing cancels downloads, closes the view
and bridge, and disposes the page before its profile. Late sends fail visibly.
An implicit shell directory is removed after page destruction; an explicit
caller output is preserved. This addresses the normal local-host lifetime;
remaining initialization/image-export resource exceptions are tracked under
`uibcdf/molsysviewer#109`.

`include_popout` is false by default. Qt child-window/popout parity remains
tracked under `uibcdf/molsysviewer#51`; browser popout tests do not qualify it.
Addon discovery and product-event routing do not certify every notebook-widget
addon panel in WebEngine. Qualify each owner's actual Qt-compatible contribution
before claiming it works in this host.

For the latest measured source scopes and retained failed attempts, see
[the standalone review](https://github.com/uibcdf/molsysviewer/blob/main/devguide/standalone_review_20261029.md).
