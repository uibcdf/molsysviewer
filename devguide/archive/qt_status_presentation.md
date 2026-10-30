---
summary: Qt status severity, lifetime and full-text access are inconsistent.
issue: uibcdf/molsysviewer#279
status: resolved
opened: 2026-10-30
closed: 2026-10-30
severity: medium
verification: reproduced
area: [standalone, qt, usability]
guard: tests/test_qt_window_polish.py::test_native_status_details_and_normal_geometry
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

## Resolution — 2026-10-30

Implemented in `7900263691cd96fcf74840357cc2e7ca8ef62914`. Explicit kind/lifetime and actual button hit-testing/copy prevent the misleading-filename and inaccessible-message failures. The companion native GPU guard also verifies full-text copying without leaving fullscreen.

Local regression covers 3,318 distinct passing cases across the original run
and directed test-provenance recovery, with 21 skips retained; 332 JS units
and 44 core browser suites pass. This is not one clean full pytest run.
Hosted CI and the postponed maintainer visual review retain their own states
in the receiving record. Qt remains experimental; no publication follows.
