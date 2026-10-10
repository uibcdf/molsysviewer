# Interaction Gestures and Menus

## Gesture Semantics

The following table captures the intended behavior.
This is the implementation contract unless superseded explicitly.

Implementation note:

- click handling must distinguish true click from drag/navigation
- in particular, empty-canvas click-to-clear must not trigger after camera manipulation
- hover highlight and persistent selection should remain visually distinct
- the canvas picking threshold is positive (`0.01`): default translucent shapes
  are addressable; fully transparent Whole ownership masks stay excluded
- hover, click and context resolve a shape's current registered owner and tag;
  atomless shapes remain selectable and visually marked as objects
- left-button drag and right-button drag already participate in canvas navigation and must remain compatible with interaction semantics

| Gesture | Target | Default effect | Selection effect | Context effect | Notes |
| --- | --- | --- | --- | --- | --- |
| Hover | `element` | update `hover_target`; temporary highlight | none | none | element target level follows current picking policy |
| Hover | `shape` | update `hover_target`; temporary highlight if viable | none | none | shape remains distinct from element picks |
| Hover | `annotation` | update `hover_target`; temporary highlight if viable | none | none | persistent labels/callouts remain their own target family |
| Hover | `empty` | clear hover target | none | none | does not clear `active_selection`; may still feed lightweight local UI reset |
| Left click | `element` | select clicked target | replace `active_selection` | none | unless `Shift` is pressed |
| Left click + `Shift` | `element` | add clicked target | add to `active_selection` | none | incremental selection |
| Left click + `Shift` + `Alt` | `element` | select range from anchor | add range to `active_selection` | none | range selection within same chain |
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

### Menu structure and dispatch

The implemented foundation of `uibcdf/molsysviewer#179` separates the target
heading from an explicitly named active-selection submenu. Molecular headings
include group and chain identifiers when available. Relevant regions are
bounded to eight entries, and saved selections open their Studio collection;
collection size does not determine the menu size. A click opens one secondary
card beside the root; another click on its trigger closes it, and selecting
another category replaces it. Hover never opens a category. Prefer the right
side, flip left near the canvas edge, and keep both cards inside the hosting
canvas. Two columns are the maximum. The active trigger stays softly highlighted.
When the canvas cannot fit both cards, the secondary replaces the root and
offers Back. Resizing switches layouts without discarding a form draft.
Each card scrolls independently; soft separators distinguish target actions,
active selection, global controls and destructive operations.

View controls, Undo/Redo and Open Studio are available across target families.
History buttons follow authoritative can-undo/can-redo state. Studio opening
selects the appropriate existing core section, including when an addon workspace
was active. Ordinary context menus do not offer Hide Canvas. Backend-owned
mutations have one event; local layout/navigation actions are consumed locally.
Viewport toggles carry the requested state so a backend echo is idempotent.

View mode choices apply their controls preset, including Cinema's bottom
trajectory scrubber and absence of viewport buttons. The canvas controls owner
uses an explicit reveal policy: `autohide_scope="controls"` by default reveals
near the buttons; `"canvas"` reveals anywhere inside the canvas. Dock, floating
and fullscreen retain the same policy. `autohide=False` keeps enabled controls
visible, and `visible=False` overrides reveal. Settings offers these choices.
When a canvas or mode first makes its controls available, show them for two
seconds so their location is discoverable, then apply the configured reveal
policy. Hover, frame updates and Dock/fullscreen changes do not restart this
introduction. Explicit hide and Help/expanded floating Studio still take
priority. Disposal cancels the introduction timer. Cinema uses the same rule
for its available trajectory scrubber; it does not gain viewport buttons.
Hide fades the entire controls surface over 200 ms, then removes it from
painting. The fading subtree becomes inert immediately, so descendants cannot
intercept picks or retain keyboard focus. Reveal can reverse an unfinished fade.
Cinema additionally restores its original 45 px downward slide over 250 ms.
Keyboard focus and touch can reveal controls; invisible controls cannot intercept
canvas picks. Enter or Space on the reveal hotspot transfers focus to an enabled,
rendered control after the visibility reversal permits it; hidden trajectory
buttons are skipped for a single structure. Pending transfer stops on disposal,
suppression or focus leaving the hotspot. Frame updates do not override visibility.
Exports and popups use
the same renderer and release subscriptions, hotspots and Cinema elements when
switching modes or disposing the controller. A popup announces readiness after
its controller and controls are mounted.

Keyboard navigation uses arrows, Home/End and Enter/Space. Escape returns from a
submenu or closes the root menu before cancelling a tool or clearing selection.
Composers occupy the secondary card, retain native input ownership, and keep
the root visible when space permits. Cancel/Escape restores their originating
submenu; another Escape returns to the root. Escape on a native select belongs
to its dropdown. Unavailable menu actions remain reachable by arrow keys,
expose `aria-disabled` and a visible explanation on focus, and reject activation
by Enter, Space or click. Native disabled form controls retain native semantics.
Closing restores focus to the previous
viewer element when focus was inside the menu. Opening and dismissal preserve
the scene and active selection.

Molecular targets support read-only inspection in System, explicit selection
replace/add/remove by atom/group/chain, and direct region/annotation composers
with declared atom scope. These composers preserve active selection. Shapes
navigation stages a target anchor; Interactions navigation stages target A and
opens an existing-data or calculation workflow without computing or applying a
filter. Calculation starts at current structure and requires an explicit name
and submission. Target/frame snapshots are dismissed on load/clear/frame change.
Only uniquely identified atom picks enable the individual-atom measurement
policy; ambiguous subsequent picks do not satisfy that policy. The three
measurement actions share an explicit endpoint-policy selector and policy-aware
pick progress. Atomless targets cannot advertise executable atom selection.
Focus uses real geometry bounds where available; otherwise it is disabled.
The active-selection submenu exposes focus, save, region/section creation,
label creation, expand and clear. Atom-dependent actions are disabled for
selections containing only scene objects. Region/label composers use the
existing replayable Python owners. Interactive measurements already create
managed objects; there is no redundant Persist Last Measurement menu action.

Object menus route annotation text/appearance, shape appearance and measurement
inspection/editing to their existing Studio owners. Selecting associated atoms
is explicit and disabled without an atom anchor. Contextual Hide carries an
explicit hidden state and is idempotent; Studio Show/Hide retains its toggle.
Related regions offer bounded access to their existing Studio inspector.

Public molecular scopes use **Atom, Group and Chain**, following MolSysMT's
topological levels. Group covers amino acids, nucleotides, waters, ions and
ligands; it is distinct from a user-defined Region. Select uses scope headings
with short replace/add/remove labels; accessible action names retain the scope.
Target composers and System inspection use the same Group terminology.
Canonical scope resolution refuses a target with no declared group/chain
membership before changing selection or creating objects. Target scope remains
available; Atom scope requires a uniquely identified atom. Rendered molecular
labels do not establish native membership.

Native loads preserve missing group/chain membership before geometry defaults.
Select disables an unavailable scope with a focus explanation; region and
annotation composers disable the corresponding option with an explanatory
label. Available target/atom scopes remain usable. Hierarchy projections retain
this availability in a popped-out Studio. Old payloads with unknown availability
still use canonical backend validation. Menu creation consistently says
Annotation; the rendered label remains an annotation kind.

Shapes and measurements use the current user-assigned tag as the primary menu
heading, with their object category below it. Related-region rows expose focus,
Show/Hide and Open in Studio; rename/delete stay in the Studio region editor.
Hover uses a soft background and keyboard focus retains a visible outline.

An interaction pick carries its analysis name/revision, filtered-query revision,
frame, occurrence ID and position in that frame query. The position is a hint:
Python validates revisions/current frame, requests one bounded inspector page,
and verifies the exact occurrence ID before inspecting/selecting/focusing.
Skipped geometry and multiple rendered segments do not redefine query positions.
Participant actions use canonical provider atoms, never client-supplied atom lists.
Graphical-set focus/hide/edit/delete is separately labelled; removing a
representation does not delete its stored analysis. Accepted interaction
summary/frame updates dismiss an open occurrence menu. Legacy projections without
the full identity disable occurrence actions instead of falling back to atom lists.

Empty canvas adds Focus All through the existing Mol* camera owner, preserving
orientation. Help reuses the overlay owned by the canvas controls and is disabled
in a host with no help owner. Host authority still limits supported operations.
[The implementation plan](canvas_context_menu_pre_1_0_plan.md) tracks automated
and human acceptance. Global picking preferences remain post-1.0; region
hide/disable and Whole ownership remain unchanged.

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

**The Python-bound hover projection is deduplicated, and must stay that way.**
Mol\* re-emits hover on every resolved pick without comparing `prevLoci`, so a
resting mouse sent roughly 30 identical messages per second to Python. The host
now drops repeats of the same target before projecting; local UI is unaffected
and still sees every event. Measured during the 2026-07 critical review.

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
