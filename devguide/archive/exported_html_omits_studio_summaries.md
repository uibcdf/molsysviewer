---
summary: Exported HTML omits Studio summaries and disables valid region controls.
issue: uibcdf/molsysviewer#130
status: resolved
opened: 2026-10-01
closed: 2026-10-01
severity: medium
verification: reproduced
area: [export, panels]
guard: tests/test_static_export_snapshot.py::test_static_export_preserves_complete_panel_summaries_without_duplicate_scene_operations
normative:
blocked_by: []
supersedes: []
---

# Exported HTML omits Studio summaries

**Reported:** 2026-10-01, actual Chrome reopening of a pentalanine HTML artifact.

## What

A hidden region configured with `representation="spacefill"` has actual Mol*
spacefill cells after reopening. Studio nevertheless disables its Show button
and calls it a base region without a representation. The inline and shared
export routes use the same incomplete snapshot.

## How

`_build_static_export_snapshot()` includes the canvas profile and interactions
and addon summaries, but omits the general panel profile. TypeScript's fallback
region summaries lack representation metadata. Include current panel summaries,
filtering operations already in the canvas profile. Preserve the static
interaction series' final summary and the live popup profile separation.

## Why

A hostless artifact must describe its scene correctly. A Python-owned command
must explain the need for a running session when clicked; a falsely disabled
control prevents that explanation.

## What was refuted

The representation itself is not missing: actual Mol* cells report spacefill,
and the browser verifies periodic interaction geometry on three frames. The
first test used the hidden floating shell's close button; using the visible
viewport Panel button revealed the disabled region control and its explanation.

## Resolution

Static export now carries the authoritative panel profile as well as the
canvas profile. Operations already carried by the canvas are filtered out;
the Interactions summary follows installation of its static frame series.
The addon summary has one source, within the panel profile. Live popup
canvas/panel separation is preserved.

The real pentalanine pytest guard asserts complete, equal panel summaries,
including the hidden region's spacefill metadata, one copy of selections and
settings, unchanged source scene and unchanged live canvas profile. The four
static-snapshot tests pass, including history-independent content/size. Removal
of duplicate filtering makes the guard fail; exact source bytes are restored.

Actual inline and shared HTML artifacts reopen in Chrome with a truthful
region Show control. Clicking it produces the running-session explanation and
leaves the hidden scene unchanged. The viewport Panel button is used to open
Studio; the floating shell's close button is not a launcher.

Validation: full Python 2,330 passed / 20 skipped, JS units 293/293,
TypeScript checking, runtime build, core browser 36/36 and both performance
harnesses pass. These are development-checkout observations; public
Interactions/provider and exact release qualification remain separate.
