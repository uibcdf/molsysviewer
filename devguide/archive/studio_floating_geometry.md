---
summary: Floating Studio recenters on unrelated layout changes and leaks its host observer
issue: uibcdf/molsysviewer#183
status: resolved
opened: 2026-10-09
closed: 2026-10-09
severity: medium
verification: reproduced
area: [studio, lifecycle]
guard: molsysviewer/js/tests/e2e/studio-usability.e2e.ts
normative: devguide/studio_interaction_contract.md
blocked_by: []
supersedes: []
---

# Floating Studio recenters on unrelated layout changes and leaks its host observer

**Reported:** 2026-10-09, source review and real Mol*/Chromium Studio audit.

## What

A real drag followed by Unlock background recentered the card. updateLayout calls centerPanel unconditionally in floating mode. The constructor host ResizeObserver is not retained or disconnected at disposal.

## How

Preserve floating bounds across background, minimize and dock changes; clamp on host resize. Own and dispose observers and outstanding drag listeners.

## Why

The Studio card is a public interactive surface being reviewed before 1.0.

## What was refuted

No claim of installed artifact qualification is made by this development review.

## Resolution

FloatingPanelShell retains floating bounds on dock/float and clamps them on host resize instead of recentering. Disposal disconnects the host observer and releases active global mouse/touch drag listeners. The real-browser guard measures bounds across drag, lock, minimize and dock/float; resize and disposal assertions reject geometry reset and leaked active handlers.

Source validation and its limits are recorded in
[the Studio integration review](../studio_review_20261009.md).
0.25.0 remains unfrozen and both 1.0 publications remain paused.
