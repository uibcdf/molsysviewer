---
summary: Applied cell feedback reissues scene geometry to every renderer.
issue: uibcdf/molsysviewer#339
status: resolved
opened: 2026-11-08
closed: 2026-11-08
severity: medium
verification: reproduced
area: [box, trajectory, popup, transport]
guard: tests/test_box_state_persistence.py::test_applied_box_feedback_updates_records_without_redrawing_the_renderers
normative:
blocked_by: []
supersedes: []
---

# Applied box feedback reissues geometry

## What

Native moving-capture traces under #319 contain repeated box clearing,
network-link creation and shape summaries while playback runs. The backend
handles every valid `box_display` receipt by calling `_follow_box_frame`, which
draws the cell again through the scene transport, including duplicate receipts
for the same cell. These are real scene barriers; follower queue experiments
cannot safely treat them as disposable frame metadata.

The real pentalanine/three-cell regression
`tests/test_box_state_persistence.py::test_applied_box_feedback_updates_records_without_redrawing_the_renderers`
fails twice before correction, for the current and a changed cell. The recipe
and canonical edges are correct, but receiving applied geometry reissues drawing
commands to both canvases. Original pytest/JUnit evidence is retained as
`query-box-feedback-before-01` in the dynamic A5 workspace.

## How

A validated frontend receipt updates the canonical cell recipe and shape
record without sending geometry again. Duplicate receipts are idempotent.
Reuse the existing scientific cell/edge conversion and recording path; do not
introduce a separate geometry implementation. Explicit Python seeks, cell/style
changes and the legacy no-projection fallback retain their normal rendering
commands. Definition revisions, invalid/stale receipt handling and cell/style
persistence remain protected by the existing box tests.

## Why

Confirmation of an applied frame is not a new scene intent. Reissuing its cell
continuously burdens the popup and can also overwrite another renderer's local
frame following. The source fix is independently required; its contribution to
the moving-save timeout still requires native receiving.

## What was refuted

The preceding requester-isolation fix remains required, but did not stabilize
capture alone. Passive frame-delivery observations measured queue delays up to
1.5 s. Separate completion lanes and bounded/coalesced follower admission also
failed their native receiving (the first prepare could start about 9.15 s after
the source request). Those alternatives are preserved with exact prototype
bytes and raw failures, then removed from the selected source. No additional
clock, pacing delay or queue reordering is shipped to conceal producer echo.

## Earlier receiving

The final affected Python box/capture/region/interaction selection passes
218/218, and the separate transport/popup/Qt-protocol/reporting selection passes
493/493. Strict frontend builds and 428 canonical Node cases pass without skips.
The unchanged native box entry exits zero in 46.24 s, receiving exported
orthogonal, rotated and triclinic cells, primary/popup navigation, explicit
cells, rebootstrap, same-frame navigation, replacement, styling, hide and clear.
All fourteen owned processes close; no resource stop occurs. Its 4,329 selected
inputs are unchanged, but that manifest omits the compiled box entry; its
post-run hash is retained separately, without a complete executed-input
immutability claim. The canonical v1 popup bootstrap/Retry guard also passes
on the selected source in 38.41 s with thirteen owned processes closed.

These results independently support the producer-side box correction. Moving
capture still times out in the first popup-state case and its three later roles
do not execute. The final combined native entry subsequently passes all seven moving/stopped
save cases and both presentation modes. This closes the bounded box finding;
it does not close A5. Capture version
2 and publication remain paused. The [working receipt](../dynamic_region_frame_receiving_20261108.json)
retains successful and failed source cohorts separately.

## Resolution — 2026-11-08

Resolved in reviewed source. Validated native feedback records its cell without echoing geometry. Explicit seeks still project. The original box controls and final seven-case native moving entry receive this boundary; broader A5 host/hidden/combined acceptance remains open. The [final source receipt](../moving_capture_font_and_region_receiving_20261108.json) records commands, exact input witnesses, retained failures, resource limits and cleanup. Public capture capabilities remain v1; publication stays paused.
