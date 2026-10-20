# Canvas popup contract

The notebook canvas and its external popup are two rendering endpoints of the
same session. Both mount `ui/controls.ts` and the same Mol* controller UI:
controls, trajectory widgets, Help, context menu, Studio and Workbench.
The notebook's **Open popup** action becomes **Close popup** in the external
window; it never recursively opens another canvas window. Classic's text label
may consequently occupy a different width.

## Runtime and initial state

The AnyWidget bootstrap supplies the runtime source it actually imported to
`render`. A legacy `popup_js_source` is a compatibility fallback, with lower
priority than that source, the active runtime cache and a complete widget ESM.
A live popup does not silently switch runtime versions after its host starts.
Widget disposal cancels host camera timers/subscriptions, closes endpoints and
streams before the wire closes, and suppresses later notifications. Notebook
test transport drains those final cancellation messages before closing Python.

`MolSysViewerController.getCanvasUiState()` owns the initial UI projection:
viewer/controls/panel modes, explicit visibility, autohide/scope and positions
in normal/fullscreen views. `PopupHostManager` injects it before creation,
so the first mounted controls already use the correct settings, including slow
molecular bootstraps. Shared controls own all their CSS and `H`/`V` shortcuts;
the popup canvas can receive keyboard focus like the notebook canvas.

## State and actions

Host trait changes continue through `molsysviewer-sync-ui` projections.
Popup changes emit the declared `molsysviewer-popup-ui` event, carrying only
canvas UI traits; the authenticated host updates its model and synchronizes
the other endpoints. Applying a host projection suppresses the popup's echo.
These layout preferences are outside scientific scene mutation history.

### Shared scene and local windows

The resolved viewpoint, molecular frame, scene objects and active selection
belong to the session. Pointer/wheel motion, focus/reset transitions and their
final drawn snapshot propagate in either direction. `CameraSync` observes
changed viewpoints, throttles continuous updates and consumes incoming
projections without echo. Automatic Spin/Swing uses the original canvas's one
clock; popup controllers retain the settings but follow its drawn snapshots.
During direct pointer input, an endpoint keeps its own input priority. Rendering
and transport have latency; this is convergence of applied state, not a promise
of simultaneous GPU frames or identical pixels at different window sizes.

Trajectory playback also has one original-canvas clock. Popup buttons request
the same operation; applied absolute frames propagate to the popup. Stop drains
pending frame writes before its final notification/projection. Derived geometry
must correspond to each endpoint's displayed frame after that projection.

Portable selection carries object owner kinds and tags, selected shape groups/instances and
entity references in addition to atoms. Each endpoint resolves its own Mol*
loci and applies projections without another Python intent. Atom membership
and selected subelements are replaced independently of coarse group toggle
identity. Pick identity is also retained in state/history and popup bootstrap;
legacy atom-only selections remain supported. An interaction reference from
another frame or analysis/query version cannot highlight a reused group number.
Managed callout text is explicitly pickable after creation and updates.
Re-picking an unchanged portable object still projects its selection: an edit
can replace its local representation without changing its portable identity.
Each endpoint then resolves fresh loci without adding another history entry.
Annotation replacement unregisters deleted refs from the pick registry.

Dock/Float, ambient/opacity/lock, expansion/navigation, window position and
fullscreen are local to each window. Initial layout is inherited, but subsequent
shell changes do not move or dock another window. Canvas mode, control
visibility, autohide/scope and control positions remain shared preferences.
Studio form drafts are local; accepted scene operations share Python ownership.

HTML exports retain that same frontend scene mirror and one playback/motion
clock. Selection, section movement and native viewport context actions have
portable frontend projections. Backend-dependent operations still require a
running session; a working focus or rotation action must not report a missing
Python backend.

Trajectory buttons in a live notebook emit the same Python authority intent
as the embedded canvas. Local feedback is reconciled with Python's resulting
frame projection. A relative step is not echoed back as another relative step.
Without Python, the exported host supplies its current frame on bootstrap and
projects the absolute resulting frame.
The popup inherits the host's authority availability, so an exported page's
backend restrictions remain visible in its external canvas too.

The popup's Studio panel popout reserves a window during the actual click
gesture, then emits `molsysviewer-popup-panel`. The notebook manager adopts
that window, supplies its channel and becomes its opener/authority; this avoids
depending on user activation surviving a later message handler. A panel-only
window owns its split shell and never projects that local layout back into the
notebook's panel style. It has no canvas controls or welcome card.

## Browser fullscreen boundaries

Studio popout and canvas fullscreen can be used together. Retaining fullscreen
while a new external window opens is subject to browser policy; MolSysViewer
does not guarantee identical results for both preparation orders. If opening
Studio exits canvas fullscreen, use the existing canvas Fullscreen button to
restore it. Alternatively, place Studio on its intended screen before entering
canvas fullscreen.

For 1.0, keep that existing interaction without an extra recovery control,
notification, automatic fullscreen re-entry or Window Management permission flow.
The maintainer accepted this boundary in `uibcdf/molsysviewer#249`: the ordinary
button provides sufficient recovery, so the audit closes without a runtime fix.
The browser-policy explanation remains consistent with the human observation,
not an exact reproduction of its cause on the reporter's browser version.

## Guard and qualification

`molsysviewer/js/tests/e2e/controls-visibility.e2e.ts` is the bounded core guard.
It checks real Python exported pages and `canvas-popup-scenarios.ts`, which
uses the actual AnyWidget bootstrap and a persistent real Python molecular
authority through `canvas-popup-bridge.py`. Only the notebook comm/trait
transport is adapted for Playwright; molecular operations use the real view.

Assertions cover first-mount Classic inheritance, stale legacy-source isolation,
matching controls/styles, mode changes in both directions, reveal behavior,
Help, keyboard, fullscreen, Studio, panel popout, preferences and single-step
trajectory convergence. Browser/WebGL failures are errors. Source/browser
evidence does not qualify future installed package bytes or the experimental
Qt host's distinct popup implementation (`uibcdf/molsysviewer#51`).

`canvas-popup-mirror-scenarios.ts` extends the same guard with real scientific
state: partial selections within one group, actual GPU picks and selected marker
bits for shapes/annotations, focus/reset/drag/wheel in both directions,
single-clock Spin/Swing and playback, symmetric local Dock, object visibility
and calculated Buch hbonds with frame-specific geometry. Controller capture
observes the real factories; it does not replace rendering or calculations.
The export scenario also receives context rotation and bidirectional selections
without Python. Earlier controls-only evidence for #232 does not qualify these
later scientific mirror changes.
