---
summary: Provide fullscreen control inside independent Studio popup
issue: uibcdf/molsysviewer#253
status: resolved
opened: 2026-10-21
closed: 2026-10-21
verification: reproduced
area: [popup, ui, interaction]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Provide fullscreen control inside independent Studio popup

**Reported:** 2026-10-21, TcTIM pre-1.0 dogfooding.

## What and how

Diego requests a fullscreen button in the independent Studio/Add-ons popup. isPanelOnly deliberately omits canvas controls; the shell currently has no fullscreen action. Closed #232 covers the external canvas, and #249 accepts browser-controlled exit while opening windows; neither implements this request.

Add a header-only control for panel-only windows. Reuse the shared fullscreen icons and existing controller action; update label, icon and pressed state from fullscreenchange. Fullscreen is window-local and listeners must be released on shell disposal. No automatic re-entry, screen-management permissions or canvas controls in the Studio-only window.

## Receiving plan

The bounded controls-visibility browser guard will cover keyboard Enter/Space, button and external Fullscreen API exit, state labels and locality in Studio popped out from both the notebook and the external canvas. Native physical-window Esc behavior remains distinct from the API event check.

## Resolution

Panel-only shell headers now offer Fullscreen/Exit Fullscreen using shared icons and the existing controller action. The listener tracks fullscreenchange and is released on disposal. The actual Python/widget/Mol*/Chromium guard exercises Enter, Space, click and external Fullscreen API exit from Studio opened through both the notebook and the external canvas, checking labels/pressed state and window locality. It does not certify a physical native Esc keystroke or change the accepted #249 browser boundary.

The bounded guard is `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`.
TypeScript, JS 330/330 and all three integrated browser scenarios pass; runtime
is rebuilt with `build:runtime`. [Receiving scopes](../studio_chrome_validation_20261021.json)
retain the open #251 caret investigation, human retest and hosted/installed
qualification separately. No new Python API, release or Qt qualification.
