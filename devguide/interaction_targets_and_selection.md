# Interaction Targets and Selection

## Target Taxonomy

Canvas interactions should distinguish these target sources:

- `empty`
- `structure`
- `shape`

For structural picks, MolSysViewer should interpret the raw pick into one of
these target levels:

- `atom`
- `group`
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
- it is the most useful default for structural inspection
- it avoids overfitting interaction semantics to atomistic representations only

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

### `context_target`

- defined by right click / context-menu invocation
- does not need to match `active_selection`
- is the anchor for context menus and command launching
- should eventually be queryable from Python, even if the first implementation only uses it internally

### `active_selection`

This should be a public object, not just hidden frontend state.
Its name should be:

- `active_selection`

It should be queryable and then usable programmatically.

The object should support at least:

- structural selections
- shape selections
- mixed selections

`mixed` should be understood broadly enough to cover:

- structure + shape mixtures
- and, if needed, mixtures of structural target levels before later normalization rules are finalized

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

## `active_selection` Contract

### Decided

- `active_selection` should be an object
- it should be able to represent `mixed` selections from the beginning
- left click replaces the selection unless `Shift` is pressed
- `Shift + left click` adds to the active selection
- left click in empty canvas, if no drag occurred, should clear the active selection

### Why mixed selection is accepted from the start

- structure and shapes are both meaningful inspection targets
- rejecting mixed selection would force a later redesign of the selection model
- operations can decide whether they apply to:
  - the whole mixed selection,
  - only the structural part,
  - only the shape part,
  - or not at all

### Proposed minimum shape of `active_selection`

At a minimum, the object should be able to expose:

- `source_kind`
  - `empty | structure | shape | mixed`
- `target_level`
  - `atom | group | chain | molecule | entity | shape | mixed | none`
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

### Structural aggregation rule

If the selection is made at `group` level, the object should still aggregate and
expose derived structural indices.

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
- plausible values include `auto`, `group`, `atom`, and other structural levels if they become product-relevant

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

- `source_kind: "structure"`
- `target_level: "group"`
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

Potentially useful later, if reliable:

- `group_type`
  - for example amino acid, nucleotide, water, ion, small molecule

Contract note:

- structural index arrays are the hard contract
- human-readable names/ids should be provided whenever reliably available
- name-like metadata should therefore be treated as strongly desired but not as the only stable source of identity
