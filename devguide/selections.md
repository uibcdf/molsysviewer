# Selections

This page defines persistent named selections as a first-class category in
MolSysViewer.

## Why `selections` Must Be Their Own Category

`regions` already carry a scene-facing meaning:

- they are structural subsets with a viewer identity,
- they can have a representation,
- they can be shown/hidden as scene objects.

Persistent named selections should be different:

- they should exist even when no visual representation is requested,
- they should preserve the result of an exploratory interaction,
- they should be reusable as input for later operations,
- they should stay reproducible across rebuild/export.

So the viewer taxonomy should now be:

- `elements`
- `selections`
- `regions`
- `shapes`
- `annotations`
- `layers`

## Relationship Between `active_selection`, `selection`, and `region`

- `active_selection`
  - transient interaction state
  - what the user is currently working with
- `selection`
  - persistent named capture of that working set
  - no automatic scene representation
- `region`
  - persistent structural object with scene meaning
  - may have representation and visibility semantics

This yields the intended progression:

- explore interactively
- obtain an `active_selection`
- persist it as a named `selection`
- optionally turn that `selection` into a `region`, `annotation`, or analysis artifact

## First Implementation Slice

The first slice should be intentionally narrow.

### Public manager

- `view.selections`

### Public operations

- `add(tag, *, atom_indices, items=None)` — direct-index shortcut; no MolSysMT lookup required ✓
- `add_selection(tag, selection, *, element, mask, syntax)` — MolSysMT-based selection ✓
- `add_from_active_selection(tag)` ✓
- `activate(tag)` ✓
- `tags` (property, list) ✓
- `contains(tag)` ✓
- `get(tag)` ✓
- `records()` ✓
- `count()` ✓
- `info(tag=None)` ✓
- `set_tag(tag, new_tag)` ✓
- `delete(tag)` ✓
- `clear(tag=None)` ✓

### Public per-selection wrapper

- `view.selections[tag].info()`
- `view.selections[tag].activate()`
- `view.selections[tag].focus(...)`
- `view.selections[tag].new_region(...)`
- `view.selections[tag].add_label(...)`
- `view.selections[tag].set_tag(...)`
- `view.selections[tag].delete()`

### `active_selection` bridge

`active_selection` should provide:

- `save(tag=...)`

Persistent selections should also be able to restore themselves into the
interactive workflow:

- `view.selections.activate(tag)`
- `view.selections[tag].activate()`

That keeps the main reproducible workflow short and explicit.

## Reproducibility Contract

Persistent selections should be stored by:

- `atom_indices`

That is the durable truth.

Derived indices such as:

- `group_indices`
- `component_indices`
- `chain_indices`
- `molecule_indices`
- `entity_indices`

should be treated as derived summaries and may be recomputed from the current
loaded system when needed.

This matters because live edits and rebuilds may invalidate derived indices even
when the atom-level remap is still possible.

## Visual Contract

Selections are not visual objects by default.

This is deliberate.

The first slice should **not**:

- create a region automatically,
- create a layer automatically,
- create a visible strip artifact automatically.

They remain reusable state, not immediate scene changes.

## Export and Replay

Selections should participate in replay/export as explicit viewer messages,
even if the frontend currently treats them as non-visual state.

This avoids creating a Python-only exception to the reproducibility model.

## Immediate Follow-on Uses

Once persistent selections exist, the following flows become more coherent:

- `selection -> region`
- `selection -> label`
- `selection -> focus`
- `selection -> future saved analysis`

## Deliberately Deferred

The first slice should not yet solve:

- visual representation of selections,
- selection-specific strip overlays,
- separate selection colors/styles,
- selection-specific context menus,
- arbitrary boolean algebra between named selections.
