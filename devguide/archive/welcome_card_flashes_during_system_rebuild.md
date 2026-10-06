---
summary: Welcome card flashes during progressive system rebuilding
issue: uibcdf/molsysviewer#164
status: resolved
opened: 2026-10-06
closed: 2026-10-06
severity: low
verification: inspected
area: [loading, ui, lifecycle]
guard: molsysviewer/js/tests/e2e/composite-load.e2e.ts
normative:
blocked_by: []
supersedes: []
---

# Welcome card flashes during progressive system rebuilding

**Reported:** 2026-10-06 by Diego during the remote-Jupyter human review.
The transient was observed on a drawing canvas; the mechanism below is source
inspection, not an automated browser reproduction.

## What

After loading the bundled 1VII protein, adding bundled caffeine SDF briefly
shows the Welcome card before displaying the combined molecular system:

```python
progressive.load(protein, structure_indices=[0], label="Proteína")
# Wait until the protein is visible.
progressive.load(caffeine, label="Cafeína")
```

The final display and framing are correct. Product source baseline:
`c046fca173f501c6e259761ef8f3d6b1825f17e8`; the documentation successor is
`e71eaf63a289bd9d3a8809c6cfd43e5e147f535a`.

## How

`molsysviewer/viewer/core.py::apply_system_edit` sends `clear_all`, followed
by the molecular projection. The controller dispatches that operation to
`SceneHandlers.clearAll`, which calls `removeLoadedStructure`. Removing the
structure clears `loadedStructure` and `currentStructure`, then calls
`updateWelcomeState`. That method shows Welcome whenever both references are
absent, including the temporary gap before the replacement projection arrives.

Distinguish a system rebuild in progress from a genuinely empty session using
the owning load/lifecycle contract. Preserve ordinary welcome/explicit-clear
behavior, panel-only endpoints, failed-load handling and popup synchronization.
Do not use a delay to hide the state distinction.

## Why

The public progressive-load workflow (#151) looks as though it has returned to
its initial state even though a new source is being added. Final-state browser
checks miss this visible intermediate behavior. A real browser guard must
observe intermediate DOM insertion during the complete rebuild and retain
negative controls for legitimate empty/welcome states.

## What was refuted

This report does not claim failed loading, a lost molecular source, a bad final
camera frame or missing source regions. All are reported correct in the same
human observation. Browser timing, persistence of the card and reproduction
across hosts have not been measured.

## Resolution

Resolved on 2026-10-06. Rebuilds
and prepared replacements send `clear_all` with `awaiting_structure: true`.
The controller suppresses Welcome across the intervening structure removal
and releases its pending state in loader cleanup, including failed native
decoding. Public `reset_viewer()` still declares a genuinely empty session.
The actual Mol* hierarchy determines whether a structure exists after failure.

`composite-load.e2e.ts::checkProgressiveWelcome` consumes actual Python load
messages and records every Welcome DOM insertion across three progressive
additions and a replacement: zero. A final-state-only assertion could miss
the defect, while this observer retains nodes removed before assertion.
Explicit clear and invalid loading restore one Welcome card. The array-native
suite checks success, explicit clear and decoding failure; panel-popup checks
that the panel-only endpoint remains free of Welcome. All focused browser
cases pass in real Chromium/Mol*, without opt-out.

The bounded browser guard profile is adopted in `reporting_protocol.md` and
resolved by its validator. Python's four-case usability module passes and
checks both rebuild declarations and ordinary reset. The new test initially
assumed list atom indices and an accumulating message log; the owning APIs
return tuples and reset the recorder on `clear_all`. Correcting those test
assumptions produced the passing run without changing product behavior.

Diego's human retest is pending. The previous fixed source handoff remains
historical evidence for its original SHA. #166 separately tracks the unit
DOM fixture failure found in `npm run test:js`; it is not a browser failure.

Complete browser regression passes **39/39 core suites**, with canonical
Python selected for both fixture and export paths. The once-run Python suite
returns 2,816 passed, 22 sandbox permission failures and 23 skipped in 524.08 s.
Normal pytest outside the sandbox passes the explicit 22 failed nodes. The
full Python suite is not repeated or represented as a fresh clean full run.
Exact source hashes, environment, controls and interrupted setup attempts are
retained in `devguide/load_usability_fixes_20261006.json`.
