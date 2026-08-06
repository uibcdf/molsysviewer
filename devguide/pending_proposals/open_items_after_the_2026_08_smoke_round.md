# Open items after the 2026-08 smoke-test round

**Sixteen of nineteen items are closed. Three remain, and none of them is work
an assistant can do:** A3 (validate the Qt host on a real screen), A5 (a human
looks at `34755fb9`) and E1 (hand MolSysMT the four files waiting in their tree).
All three are collected, with what they need, in
[`what_needs_a_human_2026_08.md`](what_needs_a_human_2026_08.md). D2 is a product
question, not an item.

Closed items keep one line and a pointer. Their original bodies are in the git
history; leaving them in place is what made this file misread as pending work.

**Written 2026-08-01** at the close of the JupyterLab smoke round that produced
Contracts S8 and S9 and seven fixes (`e50b7403` … `34755fb9`). **Swept and
compacted 2026-08-06.**

The sweep is worth recording. The headers had been kept current; the bodies had
not, so seven items claimed a state the code contradicted — including two marked
"broken right now" that were not broken. The lesson is not that the file was
careless: *a document claiming work remains ages exactly like a document claiming
work is pending, and only the second kind gets re-read.*

Its execution order is superseded by
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md).

## Z. ~~Broken right now~~ — both resolved, verified 2026-08-06 (2)

### Z1. ~~`molsysviewer-sync-hierarchy` is not declared in the action manifest~~ — RESOLVED

`molsysviewer-sync-hierarchy` is declared in `popup_actions`, and
`popupActionAllows` enforces it on both seams.

### Z2. ~~`camera_stranded_inside_scene` is not declared either~~ — RESOLVED

`camera_stranded_inside_scene` is declared in `actions` with category
`error`, so the Contract S9 signal reaches Python.

---

## A. Verification the rules require — 2 of 5 left (A3 and A5, both human)

### A1. ~~The full E2E suite was never run~~ — DONE

`npm run test:e2e` — all suites passed on real Chromium with SwiftShader,
no `E2E_ALLOW_SKIP`. Now 30 suites.

### A2. ~~`npm run test:perf` was not re-run after the render-path changes~~

Re-measured: unknown-message toll 0.3 ms unchanged, per-frame
dynamic-region evaluation 0.0007 ms against a 16 ms frame. Appended to
[`../performance/message_path_regression_check_2026_07.md`](../performance/message_path_regression_check_2026_07.md).

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

### A4. ~~The static HTML export was not validated either~~

It frames correctly: `radiusMax` 6.22 against a scene radius of 6.22 on a
real exported file. Pinned by `js/tests/e2e/exported-page-framing.e2e.ts`,
mutation-verified. A first measurement said otherwise and was an artefact
of Chrome's `--virtual-time-budget`.

### A5. The last fix of the round has not been seen by a human

**What.** `34755fb9` — the `clearGlobalRepresentations` no-op — landed **after**
Diego's confirmation that everything looked right.

**Why.** It touches the load path, the most central path there is, and this round
has already produced two cases where a fix arrived after the report it answered.
The failure it fixes (a dead ref, a `TypeError` from inside Mol\*, and a whole that
silently describes a destroyed structure) is exactly the kind the suites cannot see.

**How.** Load a structure, then load a different one in the same view, hide and show
the whole, and check the console is clean.

---

## B. Coverage that is missing (0 of 3 left; B1, B2 and B3 resolved)

### B1. ~~The `camera_stranded_inside_scene` signal has no test at all~~ — RESOLVED

Covered by `tests/test_runtime_seam_integration.py` and
`viewer-controller-message-refresh.test.ts`.

### B2. ~~The `getPanelPopupSize` wiring is uncovered~~ — DONE 2026-08-06

`panel-popup-welcome.e2e.ts` opens the pop-out through
`PopupHostManager.open` with `window.open` intercepted and asserts the
`features` string. Mutation-verified against the old fixed size.

### B3. ~~Nothing pins the actions the code sends against the manifest~~ — RESOLVED

`runtime-action-manifest.test.ts`, `tests/test_runtime_router.py` and
`tests/test_distribution_artifact.py` pin the code's actions against the
manifest, on both seams.

---

## C. Interaction never checked — closed

### C1. ~~S8 message deferral against the Qt connector~~ — answered 2026-08-06

Nothing defers on Qt and nothing needs to: the guarantee lives in
`QtMessageBridge` — one message in flight, released only by a *handled*
acknowledgement — and is now pinned in `tests/test_qt_transport_contract.py`
and recorded in Contract S8.

---

## D. Deferred by decision — only D2 is still a decision

### D1. ~~`lazy_json_fallback_payload` — never revisited~~ — DONE, not a decision

Not a decision: the lazy fallback was implemented, measured at 32 ms
against 1,459 ms, and archived.

### D2. `opt_in_hover_telemetry` — blocked — *Diego decides*

**What.** Filed, and waiting on one answer: what `view.hover_target` should mean
when telemetry is off.

**Why.** The proposal cannot be implemented without it — every design branches on
that answer.

**How.** Decide, record it in the proposal, then implement.

### D3. ~~The Mol\* upstream report has not been sent~~ — SENT as molstar/molstar#1903

Filed as [molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903)
after re-verifying all four claims against master at `26216e9b1`. Awaiting
a maintainer; see `report_molstar_empty_scene_camera_bounds.md`.

---

## E. Housekeeping and drift — 1 of 5 left (E1, the MolSysMT handover)

### E1. An orphan report left uncommitted in MolSysMT

**RESOLVED.** The orphan report is no longer in MolSysMT's working tree.

**What.** `../molsysmt/devguide/pending_bugs/viewer_json_conversion_deep_copies_twice.md`
was written during this round and never committed. The MolSysMT team fixed the bug
themselves and archived their own copy of the report.

**Why.** An uncommitted report for an already-resolved bug is confusing at best; if
it were committed now it would describe work that is done.

**How.** Check it against their archived copy and delete it, or commit only what
their archive does not already say.

### E2. ~~`pending_bugs` still lists item 8 as pending~~ — RESOLVED

That bug is archived; the item is a documented decision in the code.

### E3. ~~The System proposal keeps an obsolete "Interim" section~~ — MOOT (archived)

Moot — the System proposal was archived on 2026-08-05.

### E4. ~~The session memory is one commit stale~~ — UPDATED 2026-08-06 to the current state

`project_next_session.md` now points at `checkpoints.md` instead of
duplicating it.

### E5. ~~`checkpoints.md` does not know this round happened~~ — REWRITTEN 2026-08-06, 351 lines to 111

`checkpoints.md` was rewritten on 2026-08-06, 351 lines to 111, and now
carries the round and what remains.
