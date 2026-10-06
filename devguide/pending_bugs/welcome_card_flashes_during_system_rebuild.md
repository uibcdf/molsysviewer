---
summary: Welcome card flashes during progressive system rebuilding
issue: uibcdf/molsysviewer#164
status: open
opened: 2026-10-06
closed:
severity: low
verification: inspected
area: [loading, ui, lifecycle]
guard:
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

Pending. No runtime edit is made during the human review. Preserve the fixed
source handoff to MolSysMT while collecting the remaining observations.
