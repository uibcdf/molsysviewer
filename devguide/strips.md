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

### Layout direction

Preferred first direction:

- groups ordered by chain
- preferred first layout is one visual row per chain, if density remains usable

This is better than a single undifferentiated strip if multiple chains exist.

### Current implemented slice

The current runtime slice now does the following:

- renders a `GroupStrip` overlay from the currently loaded structure
- groups items by chain
- shows compact group labels
- mirrors the current `active_selection`
- allows:
  - click -> replace active selection
  - `Shift + click` -> additive selection
  - double click -> focus group in the viewer
  - hover -> mirrors into viewer highlight + hover event flow
  - right click -> opens the same viewer context menu contract used by the canvas
  - right click on a label overlay badge -> opens annotation context instead of falling through to the parent group target

The current slice does **not** yet do:

- range selection / drag selection
- region overlays
- tool-pick overlays

Annotation overlays have now started in a narrow form:

- persistent group labels can project compact marks onto `GroupStrip`
- they are still overlays, not first-class strip items
- richer overlay semantics (hover/pick/context) remain future work

This is intentional.
The first goal is to prove the shared state model (`active_selection`) and the
strip/canvas convergence, not to finish the entire strip UX in one pass.

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
