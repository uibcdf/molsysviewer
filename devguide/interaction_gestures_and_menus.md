# Interaction Gestures and Menus

## Gesture Semantics

The following table captures the intended behavior.
This is the implementation contract unless superseded explicitly.

Implementation note:

- click handling must distinguish true click from drag/navigation
- in particular, empty-canvas click-to-clear must not trigger after camera manipulation
- hover highlight and persistent selection should remain visually distinct
- left-button drag and right-button drag already participate in canvas navigation and must remain compatible with interaction semantics

| Gesture | Target | Default effect | Selection effect | Context effect | Notes |
| --- | --- | --- | --- | --- | --- |
| Hover | `element` | update `hover_target`; temporary highlight | none | none | element target level follows current picking policy |
| Hover | `shape` | update `hover_target`; temporary highlight if viable | none | none | shape remains distinct from element picks |
| Hover | `annotation` | update `hover_target`; temporary highlight if viable | none | none | persistent labels/callouts remain their own target family |
| Hover | `empty` | clear hover target | none | none | does not clear `active_selection`; may still feed lightweight local UI reset |
| Left click | `element` | select clicked target | replace `active_selection` | none | unless `Shift` is pressed |
| Left click + `Shift` | `element` | add clicked target | add to `active_selection` | none | incremental selection |
| Left click | `shape` | select clicked shape | replace `active_selection` | none | shape can be part of active selection |
| Left click + `Shift` | `shape` | add clicked shape | add to `active_selection` | none | may produce mixed selection |
| Left click | `annotation` | select clicked annotation | replace `active_selection` | none | annotation can be part of active selection |
| Left click + `Shift` | `annotation` | add clicked annotation | add to `active_selection` | none | may produce mixed selection |
| Left click | `empty` | clear selection if it was a click, not a drag | clear `active_selection` | none | current viewer behavior may also re-center after pan; treat that as compatible behavior, not yet a hard contract |
| Left click + `Shift` | `empty` | no-op | no change | none | do not clear selection on additive empty click |
| Left drag | any | rotate scene | none | none | preserve current navigation behavior |
| Right click | `element` | open viewer context menu if no drag occurred | no automatic change | set `context_target` | context target may seed tools; suppress host context menu inside canvas |
| Right click | `shape` | open viewer context menu if no drag occurred | no automatic change | set `context_target` | no automatic element translation; suppress host context menu inside canvas |
| Right click | `annotation` | open viewer context menu if no drag occurred | no automatic change | set `context_target` | annotation actions remain distinct from shape actions; suppress host context menu inside canvas |
| Right click | `empty` | optional viewer empty-context menu or nothing if no drag occurred | no automatic change | optional clear/update context target | keep minimal at first; suppress host context menu inside canvas when adopting viewer menu |
| Right drag | any | translate/pan scene | none | none | preserve current navigation behavior; no context menu |
| Middle click | any | deliberately outside the current contract | none | none | audit Mol* / browser behavior before adopting any product semantics |
| Double left click | `element` | focus target | no automatic change to `active_selection` | none | canonical focus gesture |
| Double left click | `shape` | focus target if possible | no automatic change to `active_selection` | none | may focus shape bounds |
| Double left click | `annotation` | focus target if possible | no automatic change to `active_selection` | none | only if the annotation has a meaningful anchor/bounds |
| Double left click | `empty` | not adopted yet | no automatic change | none | do not assume reset-by-default |
| Double right click | any | not adopted yet | none | none | explicitly considered, intentionally deferred |

## Right Click and Context Menus

### Decided

- right click without drag, when it happens inside the viewer canvas, should open the viewer menu without changing `active_selection`
- right click without drag should set `context_target`
- right-drag should remain available for pan/translation
- the menu should be able to operate on:
  - the `context_target`
  - and, if present, the `active_selection`

This separation is important.
A user should be able to inspect a new target via right click without losing an
existing working selection.

Important rule:

- choosing a contextual analytical action may use `context_target` as the first tool pick
- this does not require mutating `active_selection`
- opening or closing the context menu should not mutate scene state by itself
- the host context menu (for example JupyterLab) should be suppressed inside the viewer canvas when the viewer adopts right-click context handling

### Menu structure direction

The preferred design is:

- header or top section: target under cursor (`context_target`)
- main action section: actions that apply to `context_target`
- secondary section, when `active_selection` exists: actions that apply to the active selection

Current first implemented slice:

- the secondary active-selection section is now real,
- it currently exposes:
  - `Focus Selection`
  - `Create Region from Selection`
  - `Add Label from Selection` when the current selection resolves to exactly one `group`
  - `Clear Selection`
- the target section now also exposes a first generic action:
  - `Focus Target`
- for `annotation` targets, this replaces the old placeholder-only menu body
- for first-slice `shape` targets, `Focus Target` is also available when the shape exposes anchor atoms

This supports richer workflows and future submenus.

These two reproducibility-oriented actions are intentionally described as
selection actions first, not as pure frontend scene mutations:

- `Create Region from Selection`
- `Add Label from Selection`

They represent the intended bridge from exploratory interaction to explicit,
replayable viewer artifacts.

The same bridge now also exists for interactive measurements:

- the last interactive `distance` / `angle` / `dihedral` can be persisted as a
  replayable viewer artifact from Python
- the current persistence model stores the picked atom-index bundles, not an
  opaque frontend-only representation

It also implies that menu contents may depend on:

- `context_target`
- `active_selection`
- active tool/mode state
- and the composition of that active selection (`element`, `shape`, `annotation`, or `mixed`)

If right click occurs on empty canvas, a future UX may still expose actions tied
to `active_selection` or active mode state.
That possibility remains open on purpose.

Another useful future distinction:

- menu contents may differ depending on whether the `context_target` is already part of `active_selection`
- this can support more precise actions without forcing selection mutation

## Tool / Measurement Modes

The viewer should support explicit tool modes rather than overloading ordinary
clicks with hidden analytical semantics.

### Decided direction

At least these tool modes should exist conceptually:

- `distance`
- `angle`
- `dihedral`

When such a mode is active:

- picks should resolve at atom level
- picks should populate `tool_selection`
- completion of the required number of picks should create the corresponding measure/overlay
- the active mode should be visibly indicated
- pick progress should be visible, e.g. `1/2`, `2/3`, `3/4`
- `Esc` should be the expected cancellation path unless a later design replaces it explicitly

### Right-click launch pattern

The current preferred pattern is:

1. right click on a target without dragging
2. open context menu
3. choose `distance` / `angle` / `dihedral`
4. the clicked `context_target` becomes the first element of `tool_selection`
5. the mode remains active until enough picks are collected or the mode is cancelled

This solves a common UX need:

- right click should not overwrite `active_selection`
- but the clicked target should still seed the analytical workflow naturally

Measurement scope rule:

- measurement tools operate on atom-level picks
- shape-only picks do not satisfy a measurement pick unless a future explicit translation policy is introduced
- annotation-only picks do not satisfy a measurement pick unless a future explicit translation policy is introduced
- any future translation from shape or annotation picks to element picks must be explicit and target-type aware, not a hidden global fallback

Open UX note:

- a future implementation may choose whether a completed measurement exits the active tool mode immediately or remains in a repeatable mode
- that behavior is not fixed yet

## Hover Direction

Hover is intentionally lightweight in the first slices.

Future direction kept in scope:

- hover may later feed tooltips, lightweight inspectors, or similar read-only feedback
- this should remain additive and should not force persistent selection semantics
- such feedback may be satisfied partly in local JS/UI state without requiring every hover to become a heavyweight Python round-trip

## Navigation Compatibility

Current viewer behavior already suggests a navigation baseline that should be preserved:

- `left drag` rotates
- `right drag` translates/pans

Current accepted behavior also suggests:

- left click on empty canvas, after a pan, may restore the centered view state while also clearing `active_selection`

For now, only the selection-clear part is a hard interaction contract.
The recenter-after-pan behavior is acceptable and should not be broken casually,
but it is not yet a formally frozen semantic guarantee.
