---
summary: Studio remains visible in canvas popup after opening its own window
issue: uibcdf/molsysviewer#250
status: resolved
opened: 2026-10-20
closed: 2026-10-21
severity: low
verification: reproduced
area: [popup, layout, lifecycle]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative: devguide/canvas_popup_contract.md
blocked_by: []
supersedes: []
---

# Studio remains in its originating canvas popup

**Reported:** 2026-10-20, Diego's TcTIM pre-1.0 dogfooding. Both the external
canvas and Studio windows open, but the initiating canvas also keeps its Studio
panel visible. The corrected handoff is received by the real widget/Python/Mol*/Chromium guard.

## What

Open the canvas popup, open Studio/Add-ons in that canvas and use its panel
popout. Studio should leave the originating canvas while its separate window
is open, and return when that window closes. The molecular canvas stays usable.

Open/closed #232, #237, #245, #246 and #249 were reviewed. These cover control
parity, local layouts, addon lifetimes, controller access and browser fullscreen
policy; none guards this source-shell handoff. #249 remains accepted without
fullscreen intervention and does not account for this duplicate-panel defect.

## How

`popup/popup-logic.ts::onPanelPopClick` reserves a window and forwards its
handoff to the notebook. `index.ts::openPanelPopup` hides the notebook shell,
but no code hides the initiating canvas-popup shell. The browser guard checks
the new Studio window's contents, not source-shell disappearance/restoration.
The owning canvas now uses existing controller save/restore operations, hides
its shell after successful window reservation, and observes that window's close.
The ordinary panel toggle closes that detached window; endpoint disposal clears
its return observer. Blocking leaves the source shell in place.

## Why

Popout is a relocation of the panel from the originating canvas. Retaining
both copies wastes canvas space and contradicts the equivalent notebook action.
Window-local layout and scientific mirror ownership remain separate.

## What was refuted

This is not fullscreen loss or a request for Window Management permissions.
No scientific data/projection needs changing. A blocked `window.open` must not
hide the source shell; a source-window observer must not outlive its endpoint.

## Receiving plan

Extend `canvas-popup-scenarios.ts` inside the existing bounded
`controls-visibility.e2e.ts` core guard: source hide, real molecular canvas,
close/restore, blocked popup, repeated docked handoff and normal panel-control return.
Use real Python authority, widget bootstrap and Mol*/Chromium. Build runtime from
TypeScript, check TypeScript/JS and reporting/link contracts, and preserve the
scope separately from installed artifacts and experimental Qt.

## Receiving diagnosis — first browser attempt

The first attempt passes the exported controls scenario and reaches source
shell restoration, then fails an incorrect new assertion expecting Saved
Regions. The scenario had deliberately opened Settings before the handoff.
The guard now checks that same Settings editor is preserved rather than
requiring an unrelated panel change. Its second handoff uses the actual Panel
control: existing N/W shortcuts select individual panels directly rather than
invoking the general panel-toggle override. No keyboard contract changes.

## Owner follow-up

The first corrected targeted browser scenario passes. Source review also finds
that the notebook's previous `openPanelPopup` saves/hides its own shell and later
restores it even for a reserved window originating elsewhere. The handoff now
keeps notebook layout unchanged. `PopupHostManager.open` takes explicit panel
bootstrap/return options; the initiating endpoint retains close/restore ownership.
The extended browser assertions compare notebook visibility during detachment
and after return, in addition to source hide/restore and docked repetition.

## Resolution

The initiating canvas hides Studio only after successful window reservation.
Closing Studio or using the source Panel control restores that endpoint's saved
layout/editor; blocked popups leave it visible. The return observer is cleared
on pagehide. Notebook adoption keeps its own shell unchanged, while the shared
popup manager receives explicit bootstrap panel and return-owner options.
No fullscreen restoration or screen-permission flow was added.

The guard `molsysviewer/js/tests/e2e/controls-visibility.e2e.ts`, through its
real `canvas-popup-scenarios.ts` owner, now observes disappearance and return,
preserves Settings and Dock, checks blocking and repeated handoff, and compares
notebook layout during and after the operation. The targeted scenario, JS
330/330 and TypeScript pass. The integrated browser log retains all three
scenario success markers; its process exit code could not be recovered after
the intentional turn interruption. Runtime is regenerated via `build:runtime`.
[The receiving receipt](../studio_panel_handoff_validation_20261020.json) retains
the integrated browser result, initial guard-assertion diagnosis and other
validation scopes. No repeated full Python suite, experimental Qt/physical
dual-screen result or installed/release qualification is claimed. Human TcTIM
receiving and exact hosted CI remain separate from local source validation.
