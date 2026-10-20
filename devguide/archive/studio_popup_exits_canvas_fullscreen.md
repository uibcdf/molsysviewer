---
summary: Studio popout from fullscreen canvas loses fullscreen depending on preparation order
issue: uibcdf/molsysviewer#249
status: withdrawn
opened: 2026-10-20
closed: 2026-10-20
severity: low
verification: inspected
area: [popup, fullscreen, ui]
guard:
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Studio popout and fullscreen preparation order

**Reported:** 2026-10-20, TcTIM pre-1.0 dogfooding. Diego confirms
Chrome/Chromium on Linux with two displays; exact browser version is not recorded.

## What

Opening Studio popout, moving/maximizing it on one screen and then entering
canvas fullscreen on the other works. Entering canvas fullscreen first and
then opening Studio popout causes fullscreen to exit into the notebook.
Open/closed reports #232, #237, #180 and #209 were checked. They concern popup
parity, window-local layout, control reveal and keyboard focus respectively;
none covers this preparation-order transition. #249 is the owning new report.

## How

On source `6c49c6bc`, the shell button forwards `onPanelPopClick`;
`index.ts::openPanelPopup` hides the local shell and invokes
`PopupHostManager.open("panel")`. That owner calls `window.open` with width/
height only. The canvas-popup path reserves its Studio window during the click,
also without another screen's coordinates. These paths contain no request to
exit fullscreen. The ordinary scene handler exits only when requested to turn
fullscreen off. Existing browser guards test fullscreen and panel popout
separately; they do not protect this ordering.

The [Fullscreen Standard](https://fullscreen.spec.whatwg.org/#ui) permits the
browser to end fullscreen without an application call. Chromium's
[ShowCreatedWindow and AdjustWindowRectForDisplay](https://github.com/chromium/chromium/blob/main/content/browser/web_contents/web_contents_impl.cc)
call `ForSecurityDropFullscreen` for the popup's destination and restrict
cross-screen placement without Window Management permission. The
[Window Management API](https://developer.chrome.com/docs/capabilities/web-apis/window-management)
allows explicit screen placement with permission. The
[W3C usage guide](https://github.com/w3c/window-management/blob/main/HOWTO.md)
explains fullscreen companion windows. This is a platform mechanism consistent
with the report, not an exact-browser reproduction of its cause.

## Why

A dual-screen workspace should be understandable whichever setup order is used.
Browser permission and fullscreen authority constrain what Viewer can guarantee.
The browser may interrupt fullscreen to show a first-time permission prompt, so
that authorization cannot itself be assumed seamless from fullscreen.

## What was refuted

No explicit fullscreen exit was found in the popout path. A default popup moved
to another screen afterward cannot undo an exit caused during its creation.
Automatic restoration is not a portable fix: opening a popup consumes user
activation, and fullscreen requests have gesture/focus/permission constraints.
An automatic re-entry loop would also interfere with intentional Esc exits.

Browser-only diagnostics with Chrome 155.0.8059.84 did **not** reproduce the human
exit: headless and headed isolated-Xvfb same-screen probes retained DOM
fullscreen. Headless screen emulation did place the permitted popup on the
second screen; it does not qualify actual fullscreen retention on physical
displays. Initial Playwright/CDP permission-adapter setup failures are retained
separately. Neither virtual run substitutes for the reporter's real setup.
Scripts/results live in `/tmp/msv-fullscreen-studio-audit-20261020/`; their hashes
are in [the audit receipt](../studio_fullscreen_audit_20261020.json).

## Proposed next decision

Audit only; runtime is unchanged. Preserve the working popup-first/fullscreen-
second arrangement. Consider an unobtrusive user-initiated fullscreen recovery
when the browser exits, and optional feature-detected placement directly on a
user-selected different display. That enhancement requires intentional opt-in,
permission/secure-context checks, unsupported/denied/blocked fallbacks and
physical two-screen receiving. Do not silently move windows or promise universal
retention. Cover both preparation orders in original and external canvas before
closing a future implementation. Candidate/publication pauses remain.

## Resolution — 2026-10-20

Diego accepts retaining the existing behavior and closing this evaluation
without code changes. The existing Fullscreen button is sufficient to recover
the intended two-screen arrangement; another control or permission flow would
add complexity without sufficient benefit. No new recovery notification,
automatic re-entry or screen-placement integration is planned for 1.0.

Status `withdrawn` means the proposed runtime intervention is declined; it does
not claim that the observed browser behavior was repaired or reproduced in the
virtual diagnostics. The accepted boundary is recorded in
[the popup contract](../canvas_popup_contract.md#browser-fullscreen-boundaries).
This observation is not a 1.0 blocker. No new behavioral guard or scientific
qualification is claimed for this documentation-only disposition.
