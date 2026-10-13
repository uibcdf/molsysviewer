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
