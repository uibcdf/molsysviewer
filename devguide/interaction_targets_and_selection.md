# Interaction Targets and Selection

## Status (audited 2026-07-07)

This is a **living design contract**, not a finished/implemented spec. It is the
authoritative *home* for the interaction-selection model, but its parts are at
different maturity. Audited against the code on the date above (not just against the
per-section "Current runtime note" blocks):

**Implemented & verified**

- Canvas gestures: plain click = Replace, `Shift`+click = Add/**toggle** (removes an
  already-selected element), `Shift`+`Alt`+click = Range, click on empty = Clear
  (`managers/active-selection.ts`).
- `active_selection` object exposing `source_kind`, `element_level`, `target_level`,
  `items`, the six index arrays (`atom/group/component/chain/molecule/entity_indices`)
  and counts (`count_atoms/groups/shapes/annotations`) (`active_selection.py`).
- `view.hover_target` and `view.context_target` exist as **query-only**
  `InteractionTarget` objects (`info`, `is_empty`, `kind`, `atom_indices`, `tag`,
  `text`, `page_x`, `page_y`) — `interaction_targets.py`.

**Partial (decided but incomplete)**

- **Mixed** selections: only `element + annotation` is exercised;
  `count_shapes`/`count_annotations` stay `0` in the element `set()` path, and
  `active_selection.set()` always emits `source_kind="element"`. Broader mixed
  behaviour is intentionally incomplete.
- Human-readable metadata: `component_*`/`molecule_*` naming less complete than the
  contract target.
- The **final public object model** is explicitly still a "runtime slice".

**Open / not implemented**

- **`picking_level`** as a public concept is listed under "Decided" but is **not in
  the code** (no `picking_level` in Python or TS) — aspirational, not implemented.
- `tool_selection` as a first-class public object — open.
- Persistent picking-level configuration, a `bond` target policy, and
  `show_only`/`make_region` actions on `active_selection` — future direction.

Treat "### Decided" as *design intent recorded here*, not a guarantee of
implementation; the per-section "Current runtime note" blocks track what is actually
live.

## Target Taxonomy

Canvas interactions should distinguish these target sources:

- `empty`
- `element`
- `shape`
- `annotation`

For element picks, MolSysViewer should interpret the raw pick into one of
these target levels:

- `atom`
- `group`
- `component`
- `chain`
- `molecule`
- `entity`

`group` is the canonical MolSysSuite term.
It covers amino acids, nucleotides, waters, ions, ligands, and similar units.
Do not use `residue` as the primary public term in this feature design.

## Default Picking Policy

### Decided

- the public concept is `picking_level`
- default behavior should be clearly group-centric
- `auto` should exist as a policy name
- in practice, current design assumes `auto` resolves to `group` unless a later, explicit heuristic proves more useful
- the default interaction mode should therefore feel group-centric
- future user configuration may allow a persistent preferred picking level

Why:

- `group` is visible and meaningful across nearly all representations
- it is the most useful default for element-level inspection
- it avoids overfitting interaction semantics to atomistic representations only
- visible bonds/links should follow that same default policy:
  - under the default group-centric policy, clicking a bond fragment should
    resolve to the enclosing `group`, not to `empty`
  - a future explicit `bond` policy/target may be useful, but it should be
    modeled as its own semantic target instead of overloading `atom` with
    fragile half-bond heuristics

Public-semantics rule:

- representation may influence internal interpretation heuristics
- but the public picking behavior should remain as stable and predictable as possible across representation families

### Measurement exception

Measurement-oriented workflows should force atom picking.
This applies to at least:

- distance
- angle
- dihedral

So the design distinction is:

- normal inspection mode: tends to `group`
- measurement/tool modes: force `atom`

## Interaction State Model

The interaction model should distinguish four concepts:

- `hover_target`
- `context_target`
- `active_selection`
- `tool_selection`

### `hover_target`

- ephemeral
- updated by hover
- never the source of persistent scene mutation by itself
- should eventually be queryable from Python, even if the first implementation keeps it lightweight

Current runtime note:

- hover events already exist and are stored on the Python side
- a first lightweight public Python object now exists as `view.hover_target`
- current first slice is intentionally query-only:
  - `info()`
  - `is_empty()`
  - simple fields such as `kind` and `atom_indices`
- richer behavior and stronger typed target semantics still remain ahead

Scalability note (opt-in hover telemetry, implemented 2026-08-09):

- hover remains local to the browser by default, so moving across the structure
  produces zero Comm traffic when Python is not listening
- `view.on_hover(callback)` activates transport immediately; removing the last
  callback deactivates it unless `view.hover_telemetry_enabled` is explicitly true
- disabled and not-yet-sampled states are reported as `telemetry_disabled` and
  `telemetry_waiting`; neither is presented as an empty target
- local tooltips and highlighting are independent of this transport gate

The July round attacked the same flooding from a different angle and solved the
other half of it.
Mol\* re-emits hover on every resolved pick, storing `prevLoci` but never using
it to suppress, so a mouse **resting** on one atom sent ~30 identical messages
per second; `registerInteractionObservers` now deduplicates the Python-bound
projection (local UI still sees every tick). That fixes the resting mouse and
does nothing for a **moving** one: every tick is a different payload, so the
~16 messages/s during real hovering still cross the Comm channel. Deduplication
and opt-in are complementary, and opt-in is the one that addresses the case this
note was written about.

The implementation uses that explicit state, so querying `hover_target` does not
silently enable telemetry and cannot return a plausible but false empty target.

### `context_target`

- defined by right click / context-menu invocation
- does not need to match `active_selection`
- is the anchor for context menus and command launching
- should eventually be queryable from Python, even if the first implementation only uses it internally

Current runtime note:

- context-menu events already exist and are stored on the Python side
- a first lightweight public Python object now exists as `view.context_target`
- current first slice is intentionally query-only:
  - `info()`
  - `is_empty()`
  - simple fields such as `kind`, `atom_indices`, `tag`, `text`, `page_x`, and `page_y`
- action launching still continues to flow through the existing context-menu event bridge

### `active_selection`

This should be a public object, not just hidden frontend state.
Its name should be:

- `active_selection`

It should be queryable and then usable programmatically.

The object should support at least:

- element selections
- shape selections
- annotation selections
- mixed selections

`mixed` should be understood broadly enough to cover:

- element + shape mixtures
- element + annotation mixtures
- and, if needed, mixtures of element target levels before later normalization rules are finalized

Current runtime note:

- this is now partially real, not only aspirational
- current slices exist for:
  - `element`
  - `annotation`
  - `shape`
  - narrow `mixed`
- the most exercised mixed path today is `element + annotation`
- broader mixed behavior remains intentionally incomplete

### `tool_selection`

This is a temporary working selection for tool modes.
It is distinct from `active_selection`.

Examples:

- distance pick 1 / pick 2
- angle pick 1 / pick 2 / pick 3
- dihedral pick 1 / pick 2 / pick 3 / pick 4

Why separate it from `active_selection`:

- measurements should not need to overwrite the user's general working selection
- tool workflows are transient and mode-driven

Visibility decision still open:

- `tool_selection` is definitely part of the internal interaction model
- whether it becomes a first-class public Python object is still open

Working invariant:

- `tool_selection` should not overwrite `active_selection` by default

Current runtime note:

- this invariant is already implemented for the first measurement-tool slice
- `tool_selection` still remains an internal concept rather than a public object

## `active_selection` Contract

### Decided

- `active_selection` should be an object
- it should be able to represent `mixed` selections from the beginning
- left click replaces the selection unless `Shift` is pressed
- `Shift + left click` adds to the active selection
- left click in empty canvas, if no drag occurred, should clear the active selection

### Set-operation vocabulary (shared across surfaces)

`active_selection` is one shared state written by several peer input surfaces (the
3D canvas, the sequence strips, the Studio → Selection subpanel, and later the
add-on). The set operations they apply are a **cross-cutting vocabulary owned by this
contract**, not by any single surface:

- **Replace · Add · Subtract · Intersect · Invert** (plus All / None).

Currently implemented (canvas / strips, in `managers/active-selection.ts`):

- **Replace** — plain left click.
- **Add / toggle** — `Shift + left click`; the additive path *removes* an element
  that is already selected, so per-item de-selection already exists.
- **Range** — `Shift + Alt + left click`.
- **Clear** — left click on empty canvas.

Implemented extension (Studio → Selection Phase 0):

- **Subtract** — remove every incoming item from `active_selection`, using the same
  item identity used by Add/toggle. Aggregate index arrays are recomputed from the
  surviving items or, for backend atom-index operations, from
  `current_atom_indices - incoming_atom_indices`.
- **Intersect** — keep only items that are present in both the current and incoming
  selections. Aggregate index arrays are recomputed from the surviving items or, for
  backend atom-index operations, from `current_atom_indices ∩ incoming_atom_indices`.
- **Invert** — global complement operation. It requires a known universe, normally
  all atoms in the currently loaded molecular system, and returns
  `universe_atom_indices - current_atom_indices`.

Subtract and Intersect cannot be expressed by a single canvas click, so surfaces
expose them via explicit controls — implemented by the Studio → Selection subpanel
(`js/src/ui/panels/selection-panel.ts`). No new *click* modifier is
planned (`Alt`+click is avoided; Linux window managers commonly capture it).

Design principle for all surfaces: the operation is chosen at the moment of acting,
never as a persistent global "mode".

### Temporal dimension (structures / frames)

A MolSysMT system has a temporal dimension: multiple **structures** (trajectory
frames or NMR models), addressed by `structure_indices` (a real parameter of
`view.select`). `active_selection` is deliberately **atom / structural-identity**
based, orthogonal to that dimension:

- a selection is a set of atoms, **projected across all structures/frames** by
  default during visualization;
- choosing *which* structures/frames are shown is the **trajectory player's**
  responsibility (`player.py`), not the selection surfaces;
- keeping these orthogonal avoids cardinality collisions (an atom selection does not
  multiply by the number of frames).

Selection surfaces (including the Studio → Selection subpanel) therefore operate only
on the atom/structural axis; the temporal axis is out of their scope.

### Why mixed selection is accepted from the start

- elements and shapes are both meaningful inspection targets
- rejecting mixed selection would force a later redesign of the selection model
- operations can decide whether they apply to:
  - the whole mixed selection,
  - only the element part,
  - only the shape part,
  - only the annotation part,
  - or not at all

### Proposed minimum shape of `active_selection`

At a minimum, the object should be able to expose:

- `source_kind`
  - `empty | element | shape | annotation | mixed`
- `element_level`
  - `atom | group | component | chain | molecule | entity | none`
- `target_level`
  - `shape | annotation | mixed | none`
- `items`
  - selected elements retained as explicit items, not only as derived aggregated indices
  - should preserve order of incorporation
- aggregated deduplicated indices:
  - `atom_indices`
  - `group_indices`
  - `component_indices`
  - `chain_indices`
  - `molecule_indices`
  - `entity_indices`
- shape-side identifiers:
  - `shape_items` or equivalent
- simple counts:
  - `count_atoms`
  - `count_groups`
  - `count_shapes`

Current runtime note:

- the current payload already exposes:
  - `source_kind`
  - `element_level`
  - `target_level`
  - `items`
  - `atom_indices`
  - `group_indices`
  - `component_indices`
  - `chain_indices`
  - `molecule_indices`
  - `entity_indices`
  - `count_atoms`
  - `count_groups`
  - `count_shapes`
  - `count_annotations`
- but the current concrete item schema is still intentionally narrow:
  - element items are `group`-level only
  - annotation items are first-slice label items
  - shape items depend on first-slice shape metadata carried by Mol* shape loci
- this should still be treated as a runtime slice, not the final public Python object model

### Element aggregation rule

If the selection is made at `group` level, the object should still aggregate and
expose derived element indices.

Example:

- three selected groups from the same molecule
- `group_indices` contains three items
- `molecule_indices` contains one item
- `atom_indices` contains the union of the atoms in those groups

This makes the selection useful for both:

- programmatic downstream work
- menu generation with context-sensitive actions

The important rule is:

- `items` preserves what was actually selected
- `items` preserves incorporation order
- aggregate index arrays are computed views over those selected items

Future configuration direction:

- a user-facing default such as `picking_level_default` may later expose persistent policy selection
- plausible values include `auto`, `group`, `atom`, and other element levels if they become product-relevant

Current runtime note:

- the product direction is group-centric
- the runtime already behaves that way for ordinary element selection
- measurement modes still force atom-level picking

Active-selection direction:

- `active_selection` should become an object that downstream code can act on directly
- likely future actions include things such as:
  - `focus`
  - `show_only`
  - `make_region`
  - `info`
- it should also evolve naturally toward creating named or persistent selections/regions when that workflow is formalized

## Metadata Returned for `group` Picks

Minimum useful metadata for a group pick should include:

- `source_kind: "element"`
- `element_level: "group"`
- `atom_indices`
- `group_indices`
- `component_indices`
- `chain_indices`
- `molecule_indices`
- `entity_indices`

Human-readable metadata should include at least:

- `group_name`
- `group_id`
- `component_name`
- `component_id`
- `chain_name`
- `molecule_name`
- `entity_name`

Current runtime note:

- the current element-selection runtime already exposes first-slice human-readable metadata for groups, chains, and entities
- `component_*`, `molecule_*`, and richer naming remain less complete than the target contract

Potentially useful later, if reliable:

- `group_type`
  - for example amino acid, nucleotide, water, ion, small molecule

Contract note:

- element index arrays are the hard contract
- human-readable names/ids should be provided whenever reliably available
- name-like metadata should therefore be treated as strongly desired but not as the only stable source of identity
