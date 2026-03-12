# Interaction Gestures and Menus

## Gesture Semantics

The following table captures the intended behavior.
This is the implementation contract unless superseded explicitly.

Implementation note:

- click handling must distinguish true click from drag/navigation
- in particular, empty-canvas click-to-clear must not trigger after camera manipulation

| Gesture | Target | Default effect | Selection effect | Context effect | Notes |
| --- | --- | --- | --- | --- | --- |
| Hover | `structure` | update `hover_target`; temporary highlight | none | none | structural target level follows current picking policy |
| Hover | `shape` | update `hover_target`; temporary highlight if viable | none | none | shape remains distinct from structure |
| Hover | `empty` | clear hover target | none | none | no persistent mutation |
| Left click | `structure` | select clicked target | replace `active_selection` | none | unless `Shift` is pressed |
| Left click + `Shift` | `structure` | add clicked target | add to `active_selection` | none | incremental selection |
| Left click | `shape` | select clicked shape | replace `active_selection` | none | shape can be part of active selection |
| Left click + `Shift` | `shape` | add clicked shape | add to `active_selection` | none | may produce mixed selection |
| Left click | `empty` | clear selection if it was a click, not a drag | clear `active_selection` | none | keep this explicit |
| Right click | `structure` | open context menu | no automatic change | set `context_target` | context target may seed tools |
| Right click | `shape` | open context menu | no automatic change | set `context_target` | no automatic structural translation |
| Right click | `empty` | optional empty-context menu or nothing | no automatic change | optional clear/update context target | keep minimal at first |
| Middle click | any | deliberately outside the current contract | none | none | audit Mol* / browser behavior before adopting any product semantics |
| Double left click | `structure` | focus target | no automatic change to `active_selection` | none | canonical focus gesture |
| Double left click | `shape` | focus target if possible | no automatic change to `active_selection` | none | may focus shape bounds |
| Double left click | `empty` | no action or view-level focus reset later | no automatic change | none | not defined yet |
| Double right click | any | not adopted yet | none | none | explicitly considered, intentionally deferred |

## Right Click and Context Menus

### Decided

- right click should open a menu without changing `active_selection`
- right click should set `context_target`
- the menu should be able to operate on:
  - the `context_target`
  - and, if present, the `active_selection`

This separation is important.
A user should be able to inspect a new target via right click without losing an
existing working selection.

Important rule:

- choosing a contextual analytical action may use `context_target` as the first tool pick
- this does not require mutating `active_selection`

### Menu structure direction

The preferred design is:

- header or top section: target under cursor (`context_target`)
- main action section: actions that apply to `context_target`
- secondary section, when `active_selection` exists: actions that apply to the active selection

This supports richer workflows and future submenus.

It also implies that menu contents may depend on:

- `context_target`
- `active_selection`
- and the composition of that active selection (`structure`, `shape`, or `mixed`)

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

### Right-click launch pattern

The current preferred pattern is:

1. right click on a target
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
- any future translation from shape picks to structural picks must be explicit and shape-type aware, not a hidden global fallback

## Hover Direction

Hover is intentionally lightweight in the first slices.

Future direction kept in scope:

- hover may later feed tooltips, lightweight inspectors, or similar read-only feedback
- this should remain additive and should not force persistent selection semantics
