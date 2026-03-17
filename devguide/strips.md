# Strips

This page tracks the design direction for linear strip-style views in
MolSysViewer.

It exists because the canvas is not enough on its own for all inspection
workflows.
Strip views can provide a 1D complement to the 3D scene and can become a major
part of the product toward `1.0`.

## Why Strips Matter

A strip view can make several workflows easier:

- inspect groups in order along a chain or molecule
- select continuous regions more easily than in 3D
- cross-reference element order, sequence-like order, and active selection
- provide an alternative entrypoint for focus, menus, and tool modes

The reference inspiration here includes:

- PyMOL sequence strip
- Mol* sequence UI

But MolSysViewer should not copy them blindly.

## Reference Review

### PyMOL

Useful idea:

- a long horizontal, directly clickable strip over sequence/group order

Why it matters:

- it is fast
- it is easy to scan
- it supports element-level inspection beyond the 3D canvas

### Mol*

Useful idea:

- a real, interactive sequence view already exists in Mol* UI

What we want to borrow conceptually:

- wrapper/adaptor logic between element data and 1D view
- distinct visual states:
  - highlighted
  - selected
  - focused
- sequence/element synchronization
- optional panel layout

What we do not want to adopt directly:

- hard dependency on Mol* plugin UI components
- direct reuse of the full Mol* `SequenceView` as-is
- semantics tied too tightly to Mol*'s own selection manager and UI layout

Possible implementation pattern to keep in mind:

- MolSysViewer may still benefit from its own lightweight wrapper/adaptor layer between element data and strip positions
- this should be inspired by Mol*, not copied from it mechanically

## Alternatives Considered

### 1. Reuse Mol* `SequenceView` as-is

Not chosen.

Why:

- too coupled to `mol-plugin-ui`
- not aligned with MolSysViewer's Python-first public interaction contract
- not designed around `group`, `active_selection`, `context_target`, and `tool_selection`

### 2. Deeply adapt Mol* `SequenceView`

Not chosen for the first path.

Why:

- it would still keep too much UI and state coupling from Mol*
- the more it is adapted, the more it effectively becomes a rewrite

### 3. Build a MolSysViewer-native strip

Chosen direction.

Why:

- we can align it directly with MolSysViewer interaction contracts
- we can make it group-centric from the start
- we can keep it lightweight and notebook-friendly
- we can still borrow ideas from Mol* without importing its full UI architecture

## Chosen First Strip: `GroupStrip`

### Decision

The first strip should be:

- `GroupStrip`

This name is preferred over `SequenceStrip` because MolSysViewer works in
MolSysSuite terms and `group` is the central unit across:

- amino acids
- nucleotides
- waters
- ions
- ligands
- other small structural groups

## Evolving Container: `GroupPanel`

The current strip implementation proved the interaction contract, but it should
not be treated as the final product shape.

The next design step is to distinguish:

- `GroupPanel`
  - the container that can be shown/hidden
  - may later be docked or float
- `GroupStrip`
  - the strip unit rendered inside that panel
  - most naturally one strip per `chain`

This is needed because the current always-visible lower strip does not scale
well as product UI:

- it steals canvas space permanently
- it can hide useful references such as axes
- it does not scale to large proteins plus waters/ions/ligands
- each group currently consumes too much space

So the direction already chosen is:

- do not keep the strip permanently attached to the lower edge of the canvas
- evolve toward a show/hide `GroupPanel`
- keep `GroupStrip` as the internal interaction unit
- the current runtime now already uses a `GroupPanel` container with one concrete `GroupStrip` per chain
- treat the panel as an internal overlay of the viewer root, not as layout that may expand the surrounding notebook/output cell

## What `GroupStrip` Represents

`GroupStrip` should represent structural groups only.

It should not, in its first implementation, treat these as first-class strip
items:

- shapes
- labels
- user-defined regions

Instead:

- shapes and regions may later appear as overlays or marks on top of the strip
- but the primary strip model should remain structural groups

## First Implementation of `GroupStrip`

### Scope

The current implementation has now crossed the first structural threshold:

- it no longer renders a single monolithic strip body
- it renders a `GroupPanel` container with multiple `GroupStrip` instances, one per chain

The first implementation should still remain intentionally narrow.

It should:

- render structural groups in linear order
- be synchronized with interaction state
- support the same basic interaction contract as the 3D canvas when practical

Conceptual rule:

- `GroupStrip` should be treated as a second interaction surface over the same state, not just as an auxiliary read-only panel
- canvas and strip interactions should converge onto the same `active_selection` semantics instead of inventing separate selection logic

### What each item should show

At minimum:

- `group_name`
- `group_index`

Potential compact additions if visually useful:

- `chain_name`
- simple color or type mark

Ordering rule:

- strip order should follow the structural/canonical order of the loaded system
- it should not invent an arbitrary visual ordering unrelated to the molecular hierarchy

Detailed metadata should not require verbose inline text by default.
That detail can move into:

- tooltip
- lightweight inspector
- context menu

Visual principle:

- the strip should remain information-dense and scannable
- richer metadata should move into secondary UI rather than overloading each strip item

### Visual states

`GroupStrip` should eventually support distinct states for:

- hover
- selected
- focused
- context target
- tool-mode related marks when those workflows exist

And later possibly:

- region marks
- tool-mode picks
- labels/annotations
- more compact visual differentiation by `group_type`
- compact marks for `component`
- secondary cues for `molecule`

This last point matters because:

- a single chain may contain multiple molecules
- a molecule may be disconnected and therefore have more than one component

So chain order alone is not enough to communicate structural organization.

### Layout direction

Preferred first direction:

- groups ordered by chain
- the current adopted direction is one vertical strip-column per chain
- each chain strip should be independently scrollable and use the full useful panel height
- the earlier one-row-per-chain horizontal layout is no longer the intended direction

This is better than a single undifferentiated strip if multiple chains exist.

Current design preference:

- keep `chain` as the primary organizer
- move away from a permanent bottom band
- current adopted direction: left lateral sliding panel
- keep open whether a future variant should also allow a floating/acoplable mode

What is already decided is the negative case:

- do not keep the final product as a permanently visible horizontal strip at
  the bottom of the canvas

## Why Middle Click Is Not the Default Toggle

Mol* already uses the middle/wheel button path for camera interaction:

- wheel scroll: zoom
- middle drag: focus-and-zoom behavior

So `middle click` should not be adopted as the primary `GroupPanel` toggle for
now. It is too close to existing navigation semantics and risks conflicting
with camera behavior.

Preferred near-term direction:

- explicit UI affordance for showing/hiding the panel
- optional keyboard shortcut later
- revisit middle-click only if we explicitly decide to override Mol* behavior

### Current implemented slice

The current runtime slice now does the following:

- renders a `GroupStrip` overlay from the currently loaded structure
- groups items by chain
- **NEW: visualizes the hierarchy within each chain (Molecule -> Component -> Groups) using nested left-border lines.**
- **NEW: hierarchical selection by clicking on the molecule/component border markers.**
- **NEW: range selection within a chain using `Shift + Alt + click`.**
- shows compact group labels
- mirrors the current `active_selection`
- allows:
  - click -> replace active selection
  - `Shift + click` -> additive selection
  - `Shift + Alt + click` -> range selection (additive)
  - double click -> focus group in the viewer
  - hover -> mirrors into viewer highlight + hover event flow
- right click -> opens the same viewer context menu contract used by the canvas
- right click on a label overlay badge -> opens annotation context instead of falling through to the parent group target
- left click on a label overlay badge -> seeds the narrow `annotation` slice of `active_selection`
- that annotation selection can now coexist with element selection in the first mixed-selection path

The current slice does **not** yet do:

- range selection / drag selection
- region overlays
- tool-pick overlays

Annotation overlays are now functional:
- persistent group labels project compact marks ("L" badges) onto `GroupStrip`.
- badges are synchronized with the `add_label` workflow (validated via E2E).
- they support:
  - left click -> seeds `annotation` slice in `active_selection`.
  - right click -> opens annotation-specific context menu.
- multiple labels on the same group show a count (e.g., "2L").


This is intentional.
The first goal is to prove the shared state model (`active_selection`) and the
strip/canvas convergence, not to finish the entire strip UX in one pass.

## Preferred Demos For The Next Implementation Trial

The next strip/panel implementation trial should not rely only on
`demo["dialanine"]`.

Better demos already available in `molsysviewer.demo` are:

- `demo["1TCD"]`
  - richer protein-style sequence/group context
- `demo["181L"]`
  - useful second compact real structure with more realistic strip pressure
- `demo["chicken_villin_HP35"]`
  - useful for stress-testing density and panel ergonomics beyond toy systems

`dialanine` remains useful for unit-level sanity, but not for validating the
next panel/strip product direction.

## Interaction Rules

`GroupStrip` should follow the same base interaction semantics as the canvas
whenever that is sensible:

- hover
- left click
- `Shift + left click`
- right click
- double left click

### Selection behavior

Important agreed rule:

- if the first selection gesture on `GroupStrip` happens with `Shift`, and there is no existing `active_selection`, the strip should still initialize a new active selection cleanly
- if `Shift` is not pressed, the interaction starts a fresh `active_selection`

This keeps strip behavior aligned with the general selection contract and avoids
weird first-interaction edge cases.

Synchronization targets that should eventually be reflected in the strip:

- `hover_target`
- `active_selection`
- `context_target`
- `tool_selection`
- focus state

## What Is Explicitly Not in `GroupStrip` v1

Not part of the first strip implementation:

- `ShapesStrip`
- `RegionsStrip`
- shapes as first-class strip items
- labels as first-class strip items
- full contextual overlay system
- rich region editing directly in the strip

These are possible future directions, but not the right first step.

## Future Growth

### Possible overlays on `GroupStrip`

These are realistic later additions:

- region overlays
- active measurement marks
- label marks
- tool-mode pick markers

The key principle:

- the strip remains a structural-group strip
- other domains project onto it as overlays rather than replacing its core model

### Possible interaction growth

One realistic later addition is:

- range selection by drag across consecutive groups

This is attractive because it can make contiguous-region workflows much easier
than pure 3D picking.
It should remain a later addition, not a requirement for `GroupStrip` v1.

Another useful future behavior:

- if the relevant target is outside the visible portion of the strip, the strip may later bring it into view automatically or on demand

Another plausible future improvement:

- collapse/expand behavior by chain if large systems make the strip too dense

### Possible later strip types

These are not rejected forever, only deferred:

- `RegionsStrip`
- `ShapesStrip`

Current judgment:

- `RegionsStrip` is more plausible than `ShapesStrip`
- but neither should come before `GroupStrip`

## Relationship to `active_selection`

`GroupStrip` should be designed with `active_selection` in mind.

That means:

- it should not be implemented before the `active_selection` model is clear enough
- it should become another synchronized view over the same interaction state
- it should not invent a separate selection model

Important limitation for the first strip implementation:

- `GroupStrip` v1 should not try to solve atom-level measurement picking directly
- measurement modes may later project marks or state onto the strip, but the first strip should remain group-centric

This leads to the current sequencing decision:

1. define `active_selection`
2. implement the next interaction slice on the canvas side
3. implement `GroupStrip` immediately after that, as the next view built on the same contracts

## Product Rationale

`GroupStrip` is not just decorative UI.

It supports the broader product direction for MolSysViewer:

- not only a renderer
- not only an image generator
- but a molecular inspection workbench

That is why it belongs in the medium-term path toward `1.0`.


## Updated Layout Direction

The current preferred direction is now:

- `GroupPanel` as a container of vertical `GroupStrip` columns
- one strip-column per `chain`
- each strip independently scrollable
- denser cells with compact overlays

This should scale better than the earlier lower horizontal strip rows.
