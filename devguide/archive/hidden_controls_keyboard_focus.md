---
summary: Hidden canvas controls can lose keyboard focus transfer after visibility reversal
issue: uibcdf/molsysviewer#209
status: resolved
opened: 2026-10-10
closed: 2026-10-10
severity: medium
verification: reproduced
area: [controls, accessibility]
guard: molsysviewer/js/tests/e2e/controls-visibility.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Hidden canvas controls can lose keyboard focus transfer after visibility reversal

**Reported:** exact-source core 38040586615 on 32565b6d, during the authorized final Studio follow-up.

## What

After leaving fullscreen, focusing “Show canvas controls” and pressing Enter can leave focus on the hotspot instead of moving it to a visible control. The unchanged 30-second keyboard assertion fails before the PNG guard runs. The PNG guard therefore has no outcome in this run.

## How

`ControlsVisibility` reveals the surface and tries focusing its first enabled button in a single animation-frame callback. A reversal of the delayed CSS visibility transition may not yet be committed when that callback runs. The browser refuses focus on the still-hidden descendant. The callback is not retried.

An independent Chromium probe of the actual exported pentalanine scene reproduces the failure on its first hide/Enter cycle: after two frames the surface and button have computed visibility `visible`, surface inertness is false, but the active element is still the hotspot. This is not a lost key or permanently hidden surface.

## Why

Hidden-control discovery must give keyboard users access to the controls. The maintainer has accepted that behavior for 1.0; no publication is authorized by this correction. The existing shared visibility owner should perform the transfer when its real computed visibility permits it, and abandon pending work on disposal, suppression or focus moving away.

## What was refuted

Increasing the 30-second guard timeout does not retry a one-shot focus callback. The observed controls failure occurs before `studio-usability`, so it is not evidence of another PNG failure. No new GPU fallback or skipped accessibility assertion is appropriate.

Source inspection also establishes a single-structure variant: trajectory
buttons remain before the canvas buttons in the DOM, under `display: none`.
Choosing the first enabled DOM button can therefore choose an unfocusable
trajectory control even after the surface is visible.

## Implementation — 2026-10-10

The shared owner checks real computed surface visibility on animation frames,
then selects an enabled button with a rendered box and visible CSS. Pending
work stops when the controls are inert, the user moves focus away, or the
owner is disposed. No arbitrary delay or timeout increase is introduced.
The existing real-browser guard adds Enter/Space reversal checks and an
actual one-structure pentalanine export whose first focused button must be
Panel mode, skipping the hidden trajectory controls. Its original fullscreen,
fade/input, Cinema, popup and subscription assertions remain.

The first corrected guard run passes the trajectory, Enter/Space, fullscreen
and popup cases, but its newly added static-scene assertion reproduces a
remaining focus rejection even while computed visibility is visible. The
owner now confirms the actual active element after `focus()` and retries on
the next frame only while the hotspot still owns focus and controls remain
available. This handles browser focus eligibility during the CSS commit,
rather than treating computed styles as proof of a successful transfer.
The original failed run is retained; no guard wait is increased.

## Resolution — 2026-10-10

The final shared-owner correction confirms actual focus transfer, skips
unrendered/hidden candidates and retries only while the hotspot retains focus
and the surface is available. `controls-visibility.e2e.ts` passes through the
shared Chromium core runner with real pentalanine exports: both activation
keys, original fullscreen reversal, single-structure first-button ownership,
whole-group fade/input behavior, Cinema, popup and subscription cleanup.
TypeScript, runtime regeneration and harness/E2E builds pass. No deadline,
image quality or browser-failure policy changes. This source closure does not
claim a frozen candidate or installed-artifact qualification; the next hosted
core must confirm integration, and #198 still awaits its hosted PNG outcome.
