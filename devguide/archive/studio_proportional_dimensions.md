---
summary: Size floating Studio proportionally to its canvas host
issue: uibcdf/molsysviewer#255
status: resolved
opened: 2026-10-21
closed: 2026-10-21
verification: measured
area: [studio, popup, layout]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Floating Studio dimensions

**Reported:** 2026-10-21, TcTIM dogfooding.

## What

Enlarge initial Studio dimensions in ordinary and fullscreen notebook canvases
and external canvases, with one proportional sizing rule. Existing dimensions
are 75% width / 80% height, capped at 950×780 or 1100×850 in fullscreen.

## How

A reusable shell-layout operation computes 86% width / 88% height, capped at
1200×940, with a 10 px horizontal host margin and a normal/fullscreen vertical
reserve of 48/72 px per side for canvas controls (at most 20% per side on tiny
hosts). The real host, rather than global fullscreen
state, determines size. Untouched default geometry follows host resize;
deliberate drag/resize preserves the user's geometry and clamps it to the host.
Dock and panel-only layouts keep their own behavior. Popup sizing consumes the
same operation instead of repeating different constants.

## Why

Improve space for native forms and addons, keeping the background accessible.
Closed #183 prohibits unrelated recentering; #237 owns window-local layouts.
The new rule must preserve manual geometry and avoid cross-window changes.

## What was refuted

Unconditionally resizing every card on host growth would discard deliberate
placement. Increasing static pixel caps alone does not enlarge notebook cards.

## Receiving diagnosis

The first targeted guard found that `applyDisplay` calls `setMinimized(false)`
even when the card was never minimized. That method overwrote its freshly
calculated height with a legacy 68%/700 px fallback (or an older saved height).
The correction restores saved height only on an actual minimized→expanded
transition. The initial-dimension assertion guards this mechanism as well as
the new proportional rule.

The real fullscreen receiving then found that a larger centered card could
cover Exit Fullscreen: the controls themselves move 36 px inward in that mode.
The shared sizing operation now reserves that toolbar space, scoped to the
actual fullscreen host. Its fullscreenchange listener updates even when host
dimensions do not change and is disposed with the shell. The browser guard
uses ordinary clicks on Fullscreen and Exit Fullscreen; it does not force input
through an overlapping card.

## Resolution

The relevant real-browser receiving passes: exact reveal-rectangle click and
keyboard focus for #251; background-only alpha and retained foreground contrast
for #254; actual initial/host-resized dimensions, retained manual geometry and
normal fullscreen button clicks for #255. The source fix is ready for human
retest; the original intermittent blinking pixels are not independently certified
by a headless screenshot. [The receiving receipt](../studio_card_validation_20261021.json)
separates targeted, integrated, hosted and manual scopes. No release is authorized.

## Human retest — 2026-10-21

Diego confirms that the card is now larger. The requested transparency reversal is tracked separately under #254 and preserves the sizing implementation.
