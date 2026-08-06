# Open items after the 2026-08 smoke-test round

**Status:** audit evidence and item inventory. Its execution order is superseded
by
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md).

**Written 2026-08-01, at the close of the JupyterLab smoke round that produced
Contracts S8 and S9 and seven fixes (`e50b7403` … `34755fb9`).**

Nineteen items. They are not one kind of thing, and the grouping is the point:
two are **broken right now**, the next block is **verification the project's own
rules require and that did not happen**, and the last is housekeeping.

Ownership is marked where an item is a decision rather than a task.

The count grew from fourteen on a later pass, and how it grew is worth recording.
The first passes recalled *deferred tasks* — easy to list, because whoever deferred
them wrote them down. What surfaced later was **unconsidered scope** (A3, A4) and
**two defects introduced or exposed during the round** (Z1, Z2), none of which
appears on a deferral list by construction. The useful question was not "what did
we postpone" but "who else uses what we changed".

---

## Z. Broken right now (2)

### Z1. `molsysviewer-sync-hierarchy` is not declared in the action manifest

**What.** The host→popup message added so the System subpanel follows a structure
change (`adebbf4b`) was never declared in `popup_actions` in
`molsysviewer/runtime_actions.json`. The popup refuses it:

```
[MolSysViewer Popup] refused host action molsysviewer-sync-hierarchy
as projection: not declared in runtime_actions.json
```

**Why.** The relay works at bootstrap, because `molsysviewer-initial-sync` *is*
declared. The **update path is dead**: open the panel pop-out, load a different
structure in the notebook, and System keeps showing the previous hierarchy
indefinitely — precisely what that push exists to prevent.

Worth noting on the other side: the R1 guard did its job. It refused and warned
rather than accepting an undeclared action in silence, which is the whole reason
the manifest exists.

**How.** Declare the action:

```json
"molsysviewer-sync-hierarchy": ["projection"],
```

The declaration alone does not close the defect. Add a test through the real
host-to-popup seam that opens or simulates the panel pop-out, loads a second
structure and proves that System follows. Mutation-verify it by removing the
declaration. The existing `POPUP_ACTIONS.size >= 11` assertion is insufficient:
it can notice some deletions but pins neither this action nor its direction.

### Z2. `camera_stranded_inside_scene` is not declared either, so the signal never leaves the browser

**What.** The Contract S9 detection signal is emitted by the frontend as a
browser→Python event, and it was never declared in `actions` in
`runtime_actions.json`. `wrapOutbound` rejects it before it is sent:

```js
const category = categoryOf(action);
if (category === undefined) {
    // The manifest is complete; an unknown action is a contract defect.
    return { kind: "rejected", reason: "unknown-action", detail: action };
}
```

Its closest precedent, `viewer_init_failed`, *is* declared — which is what makes
this an omission rather than a design question.

**Why.** Worse than Z1, because Z1 breaks an update path while this breaks the
thing whole. The catalog entry, the Python handler and the frontend detector are
all wired to each other and to nothing: **the signal cannot reach Python at all.**

And it voids the argument that justified adding it. Camera authority rests on two
`isHidden` Mol\* params whose semantics can change without breaking the build; the
signal was to be the only thing that would notice. It would have noticed nothing.
Read together with B1 — the signal also has no test — the alarm is not merely
unverified, it is disconnected, and nothing would have said so.

**How.** Declare it in `actions` with the same category as `viewer_init_failed`,
then close B1, since a test would have caught this and a declaration without a test
only moves the silence one step further out.

**This is Z1 again, on the other seam, in the same session.** Two manifest-governed
boundaries, two new actions, neither declared. Both times the runtime guard behaved
correctly and refused; both times it refused into a console nobody was reading. That
is the argument for B3, and it should now cover *both* manifests rather than just
the popup one.

---

## A. Verification the rules require, not done (5)

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

## B. Coverage that is missing (3)

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

### B3. Nothing pins the actions the code sends against the manifest

**What.** The tests check specific, already-known actions
(`popupActionAllows("molsysviewer-sync-op", …)`). **No guard cross-checks the call
sites against the manifest** — not for `popup_actions` and not for `actions` —
which is why Z1 *and* Z2 passed 262 JS tests and 1158 Python tests.

**Why.** The manifest exists so the two ends cannot diverge — and yet a new sender
can be added without declaring it, with the divergence caught only at runtime, only
with a panel pop-out open, and only if someone is watching the console. That is the
§0 shape in the one place built to prevent it.

**How.** A test that greps the source for send call sites on **both** seams —
`notify`/`sendToPython` for browser→Python, `send`/`sendTo` for host↔popup — and
asserts every action string appears in the corresponding manifest section with a
compatible direction. Mutation check: remove one declaration and it must go red.

Two omissions in one session on two different seams is the measurement that says
this guard is worth more than the two one-line fixes it would have replaced.

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

## E. Housekeeping and drift (5)

Half an hour in total, and four of the five are documentation or handoff records
contradicting the
code — the exact failure `feedback_devguide_accuracy` warns about.

*(An E0 was added here on 2026-08-05 — "thirteen legacy popup actions outside the
shared manifest" — and removed on 2026-08-06 having been checked. It was not
true. `runtime_actions.json` enumerates all thirteen with the directions each may
carry, and `popupActionAllows` is enforced on three seams: host inbound, host
outbound and popup inbound, each rejecting through the contract-rejection channel,
with the direction matrix covered by unit tests. The claim came from a stale
sentence in the router document and was carried here without verifying it — which
is the very failure this section's own heading describes.)*

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

### E5. `checkpoints.md` does not know this round happened

**What.** The resume document — the one with its own *Resume cautions* section —
mentions neither Contract S8, nor S9, nor the smoke round. Its last recorded state
reaches `9512d02d`; twenty-four commits after it are absent.

**Why.** This is the same drift as the rest of the block, in **the one file whose
entire job is preventing it**, so its consequence is different in kind. Whoever
resumes from it will not know that two normative contracts now exist, will not know
that Mol\* no longer governs the camera — and may spend time debugging why it does
not re-frame on its own — and will read the collaborator's "validate Qt in a real
window" as closed without knowing that global camera behaviour changed *after* that
validation. That last one is A3, reached by reading a stale document rather than by
overlooking scope.

**How.** A new entry with the round, the two contracts, the eight defects and the
verification state; plus a line in *Resume cautions* recording that camera authority
has been ours since `75069724`.

---

## Checked, and not items

Recorded so they are not raised again.

- **`initial_messages` and the `ready` replay do not double-apply.** The trait is
  populated only for the HTML export (`build_html`); in a live widget it stays empty
  and Python's replay on `ready` is the only path. The suspicion was reasonable —
  `index.ts` enqueues the trait and *then* sends `ready` — but the two never overlap.
- **The Qt render check on a GPU runner is not missing**, it was deliberately moved
  to post-1.0 in `9512d02d`: the render itself is validated on real GPU and the CI
  job is classified non-blocking. A3 is about a *later* change invalidating that
  validation, which is a different thing.

---

## Suggested order

**Z1 and Z2 first** — one line each, and the only items that are actually broken.

**Then A1–A5.** They are minutes of runtime and could be hiding a break introduced
during the round. Within them, **A3 and A4 matter most**: they are not missing tests
but unconsidered scope, and both are shipped surfaces.

Then **B3**, because it is what would have caught Z1 and will catch the next one;
then **B1 and C1**, real gaps in guarantees rather than in tidiness.

Then **E**, which is cheap — but **E5 first within it**, and not because it is
urgent. The rest of E is a document contradicting the code, which wastes the reader
a few minutes. E5 is the resume document missing an entire round, which sends the
reader off in the wrong direction with confidence.

**D** whenever Diego decides; two of the three are his.
