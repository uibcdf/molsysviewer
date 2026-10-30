---
summary: Qt status severity, lifetime and full-text access are inconsistent.
issue: uibcdf/molsysviewer#279
status: active
opened: 2026-10-30
closed:
severity: medium
verification: reproduced
area: [standalone, qt, usability]
guard:
normative:
blocked_by: []
supersedes: []
---

# Qt status presentation

## What

The status label inferred severity and duration from message text. A real Qt
probe classified a successful `error.png` export as a persistent error, left a
`loading.png` export active indefinitely and expired an interrupted download.
Its mouse-transparent label prevented ordinary tooltip targeting; fullscreen
hid the entire header.

## How

`standalone_qt/status.py` supplies explicit string-compatible status records.
Downloads, exports and bridge delivery publish their actual kind. The native
dispatcher preserves that kind rather than reinterpreting the plain QStatusBar
signal. The keyboard-focusable status button opens a nonmodal full-text/copy
window; fullscreen gets a bounded details affordance. Ready hides presentation
without deleting the last meaningful message. No graphics/environment change.

## Why and receiving

A filename must not define failure semantics, and a truncated error must remain
readable without leaving fullscreen. The real widget guard checks those
counterexamples, lifetime and hover/copy behavior. The visible Wayland/WebEngine
guard checks actual full-text copying with fullscreen preserved, shared Help,
ten binary replacements and independent hosts. The current contract and
[receipt](../standalone_window_polish_receiving_20261030.json) retain source,
native/offscreen and broader gate scope.
