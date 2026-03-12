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
- cross-reference structure, sequence-like order, and active selection
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
- it supports structural inspection beyond the 3D canvas

### Mol*

Useful idea:

- a real, interactive sequence view already exists in Mol* UI

What we want to borrow conceptually:

- wrapper/adaptor logic between structure and 1D view
- distinct visual states:
  - highlighted
  - selected
  - focused
- sequence/structure synchronization
- optional panel layout

What we do not want to adopt directly:

- hard dependency on Mol* plugin UI components
- direct reuse of the full Mol* `SequenceView` as-is
- semantics tied too tightly to Mol*'s own selection manager and UI layout

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

The first implementation should be intentionally narrow.

It should:

- render structural groups in linear order
- be synchronized with interaction state
- support the same basic interaction contract as the 3D canvas when practical

### What each item should show

At minimum:

- `group_name`
- `group_index`

Potential compact additions if visually useful:

- `chain_name`
- simple color or type mark

Detailed metadata should not require verbose inline text by default.
That detail can move into:

- tooltip
- lightweight inspector
- context menu

### Visual states

`GroupStrip` should eventually support distinct states for:

- hover
- selected
- focused

And later possibly:

- region marks
- tool-mode picks
- labels/annotations

### Layout direction

Preferred first direction:

- groups ordered by chain
- likely one visual row per chain, if the density remains usable

This is better than a single undifferentiated strip if multiple chains exist.

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
