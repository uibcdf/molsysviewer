# Local Qt window presentation

The accepted 2026-10-29 design keeps the local Qt host experimental and uses
the shared canvas as its only scene UI. The File/View/Export/Help window menu
is retired without a replacement application menu. Studio, the canvas context
menu and canvas controls remain the owners of visible scene workflows.

## Native responsibilities

`standalone_qt/chrome.py` creates an opaque, frameless window surround with a
quiet identity header and accessible minimize/maximize/close buttons. The
header supports system movement and double-click maximize/restore; the outer
edge supports system resizing. Qt's system operations are preferred; direct
geometry fallback is limited to non-Wayland hosts. Maximized/fullscreen windows
drop the outer resize margin; fullscreen hides the header and preserves the
shared canvas's Escape and fullscreen controls.

Palette-derived colors and scalable vector glyphs keep the header readable at
different desktop scales. The web renderer, scientific Python model, transport
and GPU configuration are unchanged. A window-wide translucency effect is not
introduced into the WebEngine composition path.

There is no permanent bottom status bar. The existing QStatusBar remains
hidden as the diagnostic message owner; the header receives its messages.
The private host status record carries an explicit `ready`, `progress`, `info`
or `error` kind. Ready hides the status control, progress remains visible,
completed information expires after seven seconds, and errors remain until a
subsequent status replaces them. Filenames and arbitrary message content never
define severity or duration. Existing string callbacks remain compatible.

The status control is keyboard-focusable and clickable. It opens a nonmodal
Status details window with selectable full text and Copy message;
Ctrl+Shift+D opens the last meaningful status even after Ready or expiry.
In fullscreen a small native details control appears for active progress/errors,
while the main header stays hidden. Opening details preserves fullscreen. The window does not claim a current molecular source
name that the shared loading path cannot reliably supply.

## Keyboard affordances

`standalone_qt/actions.py` registers QActions on the window itself, independent
of a menu bar. They call the existing loading/export owners and retain the
previous shortcuts:

| Shortcut | Operation |
| --- | --- |
| Ctrl+N | Clear to an empty view |
| Ctrl+O | Native file chooser, replacing the current system |
| Ctrl+Shift+R | Explicitly restore the last recorded desktop source |
| Ctrl+W | Close the window |
| Ctrl+1 / Ctrl+2 | Open Studio / Add-ons |
| Ctrl+Shift+S / Ctrl+Shift+E | Native HTML / figure export |
| Ctrl+Shift+D | Read or copy the last status message |

Shared Help includes a Desktop window section only when the live Qt host
supplies these capabilities. They are runtime metadata, absent from widget
preferences and portable scene snapshots. Ctrl+R is no longer bound to source
replacement.

The native reset-only context menu is not restored. The removed convenience
movie action does not define another scene workflow; Movie remains owned by
the shared UI and Python API. Demos and the recent-source list stay outside
the GUI by explicit maintainer decision. Demos remain available through
`msv.demo` and `molsysviewer-qt NAME --demo`; future GUI usefulness/placement is
uibcdf/molsysviewer#277, alongside the independent Loader proposal #265.

## Window geometry

The local host records normal geometry, screen identity and maximized state
separately. Closing maximized or fullscreen does not overwrite normal size;
startup never reopens fullscreen. Legacy width/height records remain readable.
Omitted Python/CLI width and height use the saved dimensions, falling back to
1440 by 960 logical pixels. Explicit positive pixel dimensions take precedence
and start a normal window. Geometry is bounded to the available workspace;
on Wayland, the compositor retains global placement authority. This desktop
metadata does not save the molecular system or scene.

## Receiving and scope

The guard is
`tests/test_qt_live_workbench.py::test_qt_live_workbench_full_render_gpu` with
its real native child. It checks no menu widget, hidden bottom status, header
and edge affordances, maximize/double-click restore, status/error presentation,
an actual export keyboard shortcut and native save/cancel dialogs, actual
Studio source loading, fullscreen/Escape, changing molecular pixels, binary
loads and independent-window close/cleanup. The removed fake-window test
asserted the retired menu layout; actual-window receiving now owns that seam.

The first native attempt sent restore while Wayland was still applying the
maximize configure. A real widget probe confirmed the order: requested state,
restore request, then the outstanding compositor maximize configure. The
guard receives the actual resize before its next gesture; no sleep or graphics
workaround is added to production. The corrected desktop guard passes; five
affected X11/SwiftShader cases also pass. The original failed attempt remains
in the local task cache rather than being relabeled successful.

The full non-Qt regression passes 3,303 cases with 21 explicit skips and no
failures/errors. Forty standalone contracts and 295 reporting/link checks
pass; all 3,004 frozen provider hashes remain unchanged. The
[machine receipt](standalone_window_receiving_20261029.json) retains exact
source hashes, native/X11 scopes, the original failed attempt and hosted status.

Hosted [Qt run 40956603201](https://github.com/uibcdf/molsysviewer/actions/runs/40956603201)
passes all 13 distinct cases on functional commit `3283086a`: no failures,
errors or skips. The original artifact ZIP 12932774299 matches GitHub's
SHA-256 `65ad0ddb4f776ec2beb9af472b626893713fb16f8c5e962adbed6d6d288893e9`.
Its deduplicated report verifies the new frame, actual export shortcut, Studio
loading and changing molecular pixels, alongside the prior binary/authority
checks. The installed provider is public MolSysMT 0.23.0 `pyabi3h03bb3b7_0`,
with Python 3.13 and canonical Qt 6.11.2. This is not a new canonical Viewer
artifact qualification. The browser campaign 40956603291 also passes. General
CI 40956603280 and source-pair 40956603207 finish with failures: every failed
job reports the same three documentation examples raising Pandas4Warning from
`Bonds_DataFrame.sort_values(inplace=...)`, tracked by uibcdf/molsysmt#431.
The receipt preserves their terminal states; overall CI is failed. This review
changes no warning policy or provider route.

On 2026-10-29, the maintainer reports that the new window looks very good and
appears to function adequately after receiving the manual checklist. This
records positive visual and general-use feedback; individual move/resize,
minimize/restore and multi-screen outcomes were not separately enumerated.
The explicit ten-replacement human observation required by #35 remains open.
Native Windows/macOS, installed artifacts,
resource exceptions and Qt popouts retain #109/#113/#51. The remote-session
preview retains its separate shell and support boundary. This local redesign
does not certify those surfaces or change the 1.0 support promise.

Alternative hosts are a separate post-1.0 evaluation under
uibcdf/molsysviewer#276. The old
[host comparison](standalone_host_plan.md#host-options-considered) and
[v2 vision](standalone_v2_evolution_plan.md) supply context, not a requirement to
migrate or remove Python in order to modernize this window.

Startup diagnostics have a separately reproduced environment issue under
[#278](pending_bugs/qt_dbus_conda_prefix_address.md): the Conda D-Bus library
uses a relocated system address containing an unescaped `@`. The separate GBM
to Vulkan diagnostic is not evidence of CPU rendering. No graphics setting or
persistent bus configuration was changed during diagnosis.

## Polish receiving — 2026-10-30

Issues #279/#280/#281 own the explicit statuses, accessible fullscreen details,
normal geometry and native Help refinement. The [new receipt](standalone_window_polish_receiving_20261030.json)
keeps the native Wayland/WebEngine result, offscreen widget boundaries, source
reconstruction and full regression/hosted states separate. The desktop guard
observes actual click/copy in fullscreen, host Help and ten changing binary
loads; the widget guard checks misleading filenames, duration, hover targeting,
normal/maximized/fullscreen size, saved metadata, legacy restoration, explicit
dimensions and offscreen-coordinate clamping. Offscreen widget checks are not
GPU, multi-monitor or supported-platform qualification.
