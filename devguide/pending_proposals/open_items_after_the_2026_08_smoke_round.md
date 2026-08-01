# Open items after the 2026-08 smoke-test round

**Written 2026-08-01, at the close of the JupyterLab smoke round that produced
Contracts S8 and S9 and seven fixes (`e50b7403` … `34755fb9`).**

Fourteen items. They are not one kind of thing, and the grouping is the point: the
first block is **verification the project's own rules require and that did not
happen**, which is risk now rather than debt. The last block is housekeeping.

Ownership is marked where an item is a decision rather than a task.

---

## A. Verification the rules require, not done (4)

These are cheap to run and could be hiding a break introduced during the round.

### A1. The full E2E suite was never run

**What.** Twenty-eight suites are registered; only the ones touched by each change
were run individually.

**Why.** The round changed `state-handlers.ts`, `viewer-controller.ts`,
`group-panel.ts`, `group-strip.ts`, `system-panel.ts`, `popup-host.ts`, `index.ts`
and `popup-logic.ts`. That is more than enough surface to break a suite nobody
looked at, and neither the 262 JS unit tests nor the 1158 Python tests cover the
browser paths.

**How.**
```bash
cd molsysviewer/js && npm run test:e2e
```

### A2. `npm run test:perf` was not re-run after the render-path changes

**What.** The perf harness ran once, after the S8 transport change (`d0551083`),
and not after camera authority, in-place representation update, add-before-remove
or the hierarchy relay.

**Why.** `engineering_rules.md` §6 requires it for message-path work.
Add-before-remove in particular now makes two representations coexist for the
duration of a build, which is exactly what that harness measures.

**How.**
```bash
cd molsysviewer/js && npm run test:perf
```
Compare against `devguide/performance/message_path_regression_check_2026_07.md`:
unknown-message toll ~0.3–0.4 ms at 95,000 atoms, dynamic-region ~0.0008 ms/frame.

### A3. The Qt standalone host was not validated after the camera change

**What.** `takeCameraAuthority` runs in `MolSysViewerController.create`, so **every
endpoint that shares `viewer.js` inherits it** — including Qt. Its framing now
depends on `frameLoadedStructure` rather than on Mol\*'s own reset.

**Why.** This is not a missing test, it is **scope that was not considered**. Worse,
the Qt real-window validation (`e1f96509`, `903514de`, `feba4182`) predates the
change, so what was validated is no longer what ships. The same applies to the
in-place and add-before-remove representation paths.

**How.** Open a Qt window with a structure, change the whole representation, and
check the camera frames the system and the wheel zooms out. Then:
```bash
pytest tests/test_standalone.py --receptor=llm -n 12
MOLSYSVIEWER_QT_GPU_TEST=1 pytest tests/test_standalone.py   # needs a real display
```

### A4. The static HTML export was not validated either

**What.** `build_html` / `bootDocsView` builds a viewer with **no Python to ask** —
it replays a journal. It also inherits camera authority.

**Why.** If `captureCurrentStructure` does not fire the same way there,
`frameLoadedStructure` never runs and the exported viewer opens unframed. That is a
published artifact, so the failure ships.

**How.** Export a populated view, open the file, and check framing plus a
representation change. `tests/test_build_html_state.py` covers the state, not the
render, so the check is by eye.

---

## B. Coverage that is missing (2)

### B1. The `camera_stranded_inside_scene` signal has no test at all

**What.** The catalog entry, the Python handler in `_handle_frontend_event`, and
the frontend `reportStrandedCamera` all shipped with **no test** — neither that it
fires when the camera is inside the scene bounding sphere, nor that it stays quiet
when it is not.

**Why.** The entire justification for adding it was that it is the only thing that
would notice if a Mol\* release changed the semantics of the two `isHidden` params
camera authority rests on. **An untested alarm is false reassurance**, which is
worse than no alarm: it invites trust it has not earned.

**How.** Python: feed `_handle_frontend_event({"event": "camera_stranded_inside_scene",
"distance": …, "scene_radius": …})` and assert the catalog emission with its extras.
JS: drive `reportStrandedCamera` through the harness with a camera placed inside and
outside the bounding sphere and assert the notify payload. Mutation-verify both.

### B2. The `getPanelPopupSize` wiring is uncovered

**What.** The e2e asserts the size *calculation*; the one line in `popup-host.ts`
that consumes it is not covered. Stated in `923ae74c`, still true.

**Why.** A mutation of that line passed the suite, which is how the gap was found.
The size can silently revert to a fixed value with everything green.

**How.** Stub `window.open` in the e2e, open a panel popup, and assert the captured
`features` string carries the computed width.

---

## C. Interaction never checked (1)

### C1. S8 message deferral against the Qt connector

**What.** The deferral lives in `_send_widget_message`, the chokepoint **all**
connectors funnel through. Qt has had its own binary transport since `903514de`.

**Why.** If Qt shares the stream machinery, the deferral applies to it and needs the
same ordering guarantee S8 gives AnyWidget. If it does not, nothing defers there and
the contract quietly holds for one transport only. Either answer is fine; not
knowing which is not.

**How.** Determine whether the Qt path ever sets `_binary_structure_stream`. If it
does, mirror `tests/test_structure_stream_ordering.py` for that transport. If it
does not, say so in Contract S8 so the next reader does not have to re-derive it.

---

## D. Deferred by decision (3)

### D1. `lazy_json_fallback_payload` — never revisited — *Diego decides*

**What.** The JSON `ViewerJSON` payload is still built **unconditionally** as the
eager fallback, even when the array-native path carries the structure.

**Why.** Measured at roughly ten times the cost of the binary path. The proposal was
filed with the recommendation to smoke-test first; the smoke round happened and this
was never picked back up. It is real startup time on every load.

**How.** See `devguide/pending_proposals/lazy_json_fallback_payload.md`. Decide
whether the fallback is built lazily on failure, then implement and re-measure
against `devguide/performance/startup_baseline_2026_07.md`.

### D2. `opt_in_hover_telemetry` — blocked — *Diego decides*

**What.** Filed, and waiting on one answer: what `view.hover_target` should mean
when telemetry is off.

**Why.** The proposal cannot be implemented without it — every design branches on
that answer.

**How.** Decide, record it in the proposal, then implement.

### D3. The Mol\* upstream report has not been sent — *Diego sends it*

**What.** `report_molstar_empty_scene_camera_bounds.md` carries the issue title and
body, two patches and a self-contained reproduction. Nobody has filed it.

**Why.** Filing is what eventually retires the workaround **and** the runtime
detection that exists only to guard it. Until then both are permanent.

**How.** Paste it at `molstar/molstar` and record the issue number in the proposal.

---

## E. Housekeeping and drift (4)

Half an hour in total, and three of the four are documentation contradicting the
code — the exact failure `feedback_devguide_accuracy` warns about.

### E1. An orphan report left uncommitted in MolSysMT

**What.** `../molsysmt/devguide/pending_bugs/viewer_json_conversion_deep_copies_twice.md`
was written during this round and never committed. The MolSysMT team fixed the bug
themselves and archived their own copy of the report.

**Why.** An uncommitted report for an already-resolved bug is confusing at best; if
it were committed now it would describe work that is done.

**How.** Check it against their archived copy and delete it, or commit only what
their archive does not already say.

### E2. `pending_bugs` still lists item 8 as pending

**What.** The no-op `clearGlobalRepresentations` was fixed in `34755fb9`;
`camera_zoom_out_blocked_after_scene_replay.md` still lists it as work to do.

**Why.** A plan that lies about what is done sends the next person to redo it.

**How.** Mark it DONE with the commit, as items 1, 3, 5 and 6 already are.

### E3. The System proposal keeps an obsolete "Interim" section

**What.** `system_panel_hierarchy_summary.md` is marked done, but still contains
*"Interim, if this is not done soon"*, proposing a note in the System tab
explaining that the hierarchy lives with the canvas.

**Why.** It is no longer true and someone could implement it, adding a message to a
panel that now works.

**How.** Delete the section.

### E4. The session memory is one commit stale

**What.** `project_next_session.md` records `HEAD adebbf4b`; the round ended at
`34755fb9`, which is the `clearGlobalRepresentations` fix.

**Why.** Small, but it is drift in the file whose whole job is telling the next
session where things stand — and it omits the last fix of the round.

**How.** Update the HEAD and add the eighth defect to the list.

---

## Suggested order

**A1–A4 first.** They are minutes of runtime and they are the only items that could
be hiding something broken right now. Within them, **A3 and A4 matter most**: they
are not missing tests but unconsidered scope, and both are shipped surfaces.

Then **B1 and C1**, which are real gaps in guarantees rather than in tidiness. Then
**E**, which is cheap. **D** whenever Diego decides; two of the three are his.
