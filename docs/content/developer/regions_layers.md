# Regions and layers

This page documents regions, layers, tags, and visibility semantics.
These concepts are user-visible and must remain stable.

## Naming and concepts

- **Region**: a structural subset identified by `tag` (user-provided or auto). Its provenance recipe is primary; `atom_indices` is the cached result of the last evaluation.
- **Layer**: a tag-based group for non-structural visuals (shapes/overlays).
- If you do not pass a tag, MolSysViewer assigns an auto-tag (`region1`, `layer1`, ...).

## Python API (sketch)

- `view.regions.add(selection, tag=None, representation=None, **repr_params) -> Region`
- `view.new_layer(kind=None, tag=None, **meta) -> Layer`
- Public registries: `view.regions` / `view.layers` (example: `view.regions["set1"].hide()`).
- `Region`: `set_representation(...)`, `reset_representation()`, `hide()/show()`, `focus()`, `show_only()`, `delete()`, complements (`new_complementary_region()`), boolean composition, and `mode`/`provenance` metadata.
- `Layer`: `hide()/show()`, `delete()`, `set_tag()` (and possibly `merge()` in the future).
- Whole: `view.whole` (`set_representation`, `reset_representation`, `set_color_scheme`, `reset_colors`, `hide()/show()`, `focus()`), not deletable and not retaggable.
- Region builders on the viewer: `make_regions_by(element=...)` with `element in {"chain", "molecule", "entity"}`.
- Complements: `view.regions.add(..., complement_of_regions=["tagA", ...] | "all")` computes complements in Python.

## Tagging policy

- User-provided tags remain the strongest source of truth and must be preserved exactly unless a collision must be resolved.
- Auto-generated fallback tags remain sequential for ad hoc objects (`region1`, `layer1`, ...).
- For viewer-generated semantic regions such as `make_regions_by(element="chain" | "molecule" | "entity")`, the tag should be derived from a human-readable MolSysMT label when possible and then sanitized to a stable tag token.
- Preserve semantic clarity in generated tags: concise chain labels can stand alone (`A`), while broader classes should keep an element prefix (`molecule_peptide_0`, `entity_peptide_0`) to avoid ambiguity.
- If two generated tags collide, resolve the collision deterministically with suffixes such as `__2`, `__3`, ...
- Generated tags must be replay-safe and merge-safe: they should survive rebuild/export/replay and later multi-view composition without ambiguity.

## JS responsibilities

- Source of truth for Mol* refs:
  - regions: `tag -> { componentRef, reprRefs[], atomIndices[], selection, hidden }`
  - layers: `tag -> { refs, kind/meta }`
- whole reps: `globalReprs` internally, exposed through `set_whole_representation`, `show_whole`, and `hide_whole`.
- Handlers: create/set/show/hide/delete region; same for layers; set/hide/show whole; clear/reset/load cleans registries and notifies Python.
- Acks to Python: `region_ack` (includes `atom_indices` and `selection`), `layer_ack`, `registry_cleared`.
- Shapes: are tagged and registered as layers via `tagIndex`.

## Visibility (whole vs regions vs viewer)

- `region.hide()/show()`: affects only that region; the `hidden` state is remembered. `viewer.show()` must not re-enable hidden regions.
- `whole.hide()/show()`: affects only the baseline representation. It does not touch region visibility; regions in state None disappear because they have no own visual.
- `viewer.hide()/show()` with `selection="all"`: updates the atom mask. It composes with whole/region visibility and the ownership transparency mask.

Reference flows

1) Hide whole before first show
```python
view = viewer.demo["1TCD"]
view.whole.hide()
view.show()  # regions may be created; whole stays hidden
```

2) Hide one region and preserve it across hide/show
```python
view = viewer.demo["1TCD"]
r1 = view.regions.add("chain_id == 'A'", representation="sticks")
r2 = view.regions.add("chain_id == 'B'", representation="sticks")
r2.hide()
view.hide()
view.show()  # r1 visible, r2 still hidden; whole follows its flag
```

3) Hide everything and restore only what should be visible
```python
view.hide()  # hides whole + regions + atom mask
view.show()  # hidden regions stay hidden; whole follows its state
```

## Whole presets and tags: collision risk

The “whole vs region” split assumes that baseline representations do not reuse region tags.
If a custom whole preset creates representations tagged with the same tag as a region, those reps can be treated as “region reps”.
That can cause operations such as `whole.hide()` to miss them.

Recommendations

1. For whole presets, do not assign region tags. Use `tag="whole"` or no tag.
2. If you need to apply a preset to a specific region, use `region.set_representation(preset=...)`, not `whole`.
3. If you inherit from a Mol* preset and add rules, avoid tags that collide with region tags.

## Ideas

- Helpers: `get_region/get_layer/list_*`; a lightweight inspector for regions/layers and visibility.
- Preserve whole style across `load`.
- JS handler for selection strings when `atom_indices` are missing.
- JS → Python events if reps are modified outside the Python-driven flow.
- Representation coexistence modes: `replace` / `exclusive` to avoid overlaps.
- Complement validation when `atom_indices` are not yet known (acks).
- Sync the visibility mask with regions if the user called `whole.hide()` first.
