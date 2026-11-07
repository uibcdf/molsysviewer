---
summary: Visible simulation-box display is omitted from saved work.
issue: uibcdf/molsysviewer#326
status: resolved
opened: 2026-11-07
closed: 2026-11-07
severity: medium
verification: reproduced
area: [state, session, box, trajectory]
guard: tests/test_box_state_persistence.py
normative:
blocked_by: []
supersedes: []
---

# Simulation-box display in saved work

The real pentalanine control with three non-consecutive structures and explicit
3/4/5 nm cells keeps one visible `__msv_box` runtime record, but exports no box
display. A saved session reloads its scientific cells correctly and loses the
visible box. Both ready and headless controls reproduce this on `b25a4bff`.
`export_state` filters raw box history because it has no managed Shape object.

All four issue-inventory pages were checked before opening #326. #96 concerns
length units; #155 concerns provider box assignment; #263 concerns test setup.
This is a Viewer persistence defect, not a MolSysMT scientific-data defect.

## Accepted work and receiving

Under A5/#319 and #315, retain a small semantic display recipe with explicit
width units and its selected structure. Restore edges from the scientific
system; keep normal frame following, non-consecutive extraction and the
existing first-system cell rule. Do not materialize/copy a trajectory to retain
display settings. Legacy version-2 documents and atomic rejection remain valid.

**Resolved in source:** state/session display now uses a small `box_display`
recipe and regenerates edges from the retained scientific cell. The guard
`tests/test_box_state_persistence.py` covers both formats/readiness states,
exact style and cell, later frame following, remapped non-consecutive
extraction, history, clearing, legacy import and rejection without loss.
Four cases fail before the correction; substituting the wrong restored width
also fails all four. The current 551-case Python boundary selection passes,
including all 61 box cases, with 4,071 selected inputs unchanged.

The complete canonical Studio browser entry passes in 213.27 seconds with
4,299 fixed inputs and all eighteen owned processes closed. Primary, popup
and detached-Studio state/session restores first perturb the camera and frame,
then require the saved camera, frame and actual twelve-edge mesh on a new
completed draw. This required the separately received initial-fit correction
under #319. See the [bounded receipt](../box_display_receiving_20261107.json).
Continuous-playback/hidden-endpoint capture, full consolidated hosted/installed
qualification and the A5 parent remain open. The original native reproducer's
zero exit asserts the defect; it is not product acceptance.
