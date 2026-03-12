# Annotations

This page defines the viewer taxonomy around persistent labels and related
annotation-like objects.

It exists to separate semantic visual information from geometry overlays and to
avoid overloading `shapes` with text-like concerns.

## Why This Needs Its Own Category

MolSysViewer already has:

- element-derived interaction targets,
- regions,
- shapes,
- layers,
- and an emerging interaction/selection model.

Persistent labels do not fit cleanly inside `shapes`:

- they are not primarily geometry,
- their lifecycle is different,
- their context actions are different,
- their future strip/selection integration is different,
- and Mol* itself already treats labels/text as a distinct concern.

So MolSysViewer should treat them as:

- `annotations`

## Viewer Taxonomy

The intended high-level taxonomy is:

- `elements`
- `regions`
- `shapes`
- `annotations`
- `layers`

### `elements`

Element targets come from the molecular system.
They are described using MolSysSuite element levels:

- `atom`
- `group`
- `component`
- `chain`
- `molecule`
- `entity`

### `regions`

Regions are user-defined or viewer-defined subsets of elements.
They are not a separate target family in the molecular-system hierarchy.
They are named, reusable subsets over element indices.

### `shapes`

Shapes are additional geometric objects rendered in the scene.
Examples:

- spheres
- pocket surfaces
- pocket blobs
- channel tubes
- pharmacophore geometries
- links
- displacement vectors
- tetrahedra
- triangle faces

### `annotations`

Annotations are persistent semantic/visual objects that are not primarily
geometric overlays.

The first annotation family should be:

- `labels`

Future families could include:

- callouts
- badges
- text markers

### `layers`

Layers are not a content family.
They are a grouping/control mechanism for non-element scene content.

They should apply to:

- shapes
- annotations

They should not redefine the underlying taxonomy.

## What We Learned From Mol*

Mol* already provides several useful precedents.

### 1. Structure label representation

Mol* has a built-in label representation:

- [label.ts](/home/diego/repos@others/molstar/src/mol-repr/structure/representation/label.ts)
- [label-text.ts](/home/diego/repos@others/molstar/src/mol-repr/structure/visual/label-text.ts)

This shows that persistent text tied to molecular content is a first-class
visual concern, not just a tooltip.

Useful takeaways:

- text is rendered as a dedicated visual,
- labels can be generated at several levels,
- labels are not just hover UI,
- labels are intentionally non-pickable in Mol*'s default implementation.

### 2. Loci-based labels

Mol* also has labels built from explicit `loci` data:

- [shape/loci/label.ts](/home/diego/repos@others/molstar/src/mol-repr/shape/loci/label.ts)

Useful takeaways:

- a label can be defined from an arbitrary set of picked/selected loci,
- placement can come from the loci bounding sphere,
- text is built with `TextBuilder`,
- labels can be defined independently from the default structure representation.

This is directly relevant to MolSysViewer because it suggests a clean path for:

- labels anchored to element-derived selections,
- labels anchored to regions,
- labels anchored to future analysis results.

For MolSysViewer this should be interpreted carefully:

- labels may later be created from regions as a user-facing workflow
- but the underlying anchor model should still resolve to element-derived anchors
- `region` should not become a separate low-level annotation target family in v1

### 3. Custom and annotation-driven labels

Mol* MVS extensions include:

- [custom-label/representation.ts](/home/diego/repos@others/molstar/src/extensions/mvs/components/custom-label/representation.ts)
- [annotation-label/visual.ts](/home/diego/repos@others/molstar/src/extensions/mvs/components/annotation-label/visual.ts)
- [annotation-tooltips-prop.ts](/home/diego/repos@others/molstar/src/extensions/mvs/components/annotation-tooltips-prop.ts)

Useful takeaways:

- custom text labels and annotation-driven labels are separate from tooltips,
- grouping multiple annotation rows into one label instance is useful,
- text content and label placement should be separable concerns,
- tooltip behavior and persistent label behavior should not be conflated.

## Core Decision

Persistent labels in MolSysViewer should belong to:

- `annotations`

They should not be modeled as ordinary shapes.

This is the key architectural decision on this page.

## First Annotation Family: Labels

The first concrete annotation type should be:

- `label`

That first slice should stay intentionally narrow.

## Label Target Families

The long-term design can support three target families:

- element targets
- shape targets
- explicit point targets

### Element target

Examples:

- a label on a `group`
- a label on an `atom`
- a label on a derived picked/selected element set

This should be the first implementation target family.

### Shape target

Examples:

- a label attached to a pharmacophore feature shape
- a label attached to a pocket surface or analysis overlay

This is useful, but should come later.

### Point target

Examples:

- a label at a specific 3D coordinate
- a label for a pocket center or geometric feature

This should also come later.

## First Implementation Scope

### v1 should support

- persistent labels as `annotations`
- labels anchored to element targets
- `group` first
- replay-safe/export-safe persistence
- rebuild-safe persistence
- integration with existing layer semantics
- actual `clear labels` support in the frontend instead of the current placeholder
- a narrow public API:
  - `view.annotations.add_label(text=..., group_index=..., tag=...)`
  - `view.annotations.add_label_from_active_selection(text=..., tag=...)`

### v1 should not try to solve

- every annotation subtype
- atom-attached labels unless a concrete product need appears immediately
- fully general shape-attached labels
- free-floating point labels
- rich annotation editing UI
- annotation-aware mixed-selection behavior in full detail
- strip-aware label overlays

## Intended Layer Semantics

Annotations should participate in layers.

That means a layer may contain:

- shapes
- annotations

This is intended from the beginning, not only as a future possibility.

This enables:

- show/hide by layer
- clear/delete by layer
- shared analysis grouping

This is preferable to creating a parallel label-only grouping system.

Tag discipline should stay aligned with the rest of the viewer:

- tags should be stable
- tag-driven clear/hide/show should be deterministic
- annotation registration should remain replay-safe

## Intended Interaction Semantics

Annotations should eventually become their own interaction target family:

- `annotation`

This aligns with the interaction docs:

- target kinds should now be understood as:
  - `empty`
  - `element`
  - `shape`
  - `annotation`

Implications:

- annotations should be valid `context_target` candidates
- annotations should eventually be valid `hover_target` candidates when lightweight local feedback is useful
- annotations may later participate in `active_selection`
- annotation actions should remain distinct from shape actions

The first implementation does not need full annotation-selection richness, but
it should not block that direction.

## Initial Pickability Direction

Mol* defaults its built-in labels to non-pickable.

For MolSysViewer, the preferred direction is more pragmatic:

- labels should eventually be interactable as `annotation` targets
- but v1 does not need to solve full pick/selection richness from the first day

So the initial contract should be:

- do not force annotation pickability if that would destabilize the first label slice
- but do not design the rendering path in a way that makes annotation pickability impossible later

## Minimal Label Data Model

The first useful conceptual model for a label should include:

- `text`
- `tag`
- `layer`
- `visible`
- `target`

Where `target` in v1 is element-based.

For element-based labels, the target should eventually be able to describe:

- `element_level`
- relevant index arrays

The target model should preserve:

- the original anchor that the user actually labeled
- and any derived index views needed for replay, rebuild, or later operations

This mirrors a principle already present in selection design:

- preserve the semantic source of the interaction
- derive aggregate/index views second

### Text policy for v1

The initial label slice should assume:

- explicit user-provided text

Automatic text derivation from target metadata may become useful later, but it
should not be part of the first contract.

That keeps v1 predictable and avoids mixing:

- placement policy
- target identity
- text-generation policy

### Remap / invalidation policy

Labels should survive replay and rebuild while their target can be remapped
cleanly.

If a rebuild or edit removes the target anchor in a way that cannot be remapped
meaningfully, the label should:

- be invalidated cleanly
- disappear deterministically
- and avoid leaving stale/corrupt annotation state behind

This should remain aligned with the element taxonomy used elsewhere in the
interaction contract.

## Naming Direction in Python

The likely Python-side home should be something like:

- `view.annotations`

with a dedicated manager-style surface.

Possible first API direction:

- `view.annotations.add_label(...)`

Likely management direction after that:

- label creation should live under `view.annotations`
- bulk visibility/clear behavior should prefer existing layer semantics
- `clear_decorations(..., labels=True)` should remain valid as a convenience path

So the minimum management surface for v1 should effectively cover:

- add label
- clear labels
- show/hide through layers

Current API direction is now stronger than that first minimum:

- `view.annotations.tags()`
- `view.annotations.count()`
- `view.annotations.contains(tag)`
- `view.annotations.get(tag)`
- `view.annotations.records()`
- `view.annotations.info(tag=None)`
- `view.annotations.show(tag)`
- `view.annotations.hide(tag)`
- `view.annotations.delete(tag)`
- `view.annotations.set_tag(tag, new_tag)`
- `view.annotations.clear(tag=None)`

This is intentional.
Annotations should be manageable through a robust Python API, not only through
UI affordances.

Two complementary inspection layers now exist by design:

- `records()`
  - low-level replay-oriented records
- `info(tag=None)`
  - compact user-facing summaries of current annotations

That separation keeps the reproducibility layer explicit without forcing users
to parse the raw replay records for ordinary inspection.

Anything richer than that should wait until the first label slice is stable.

This is a better fit than:

- placing labels under `view.shapes`

because the category boundary stays explicit and future growth remains clean.

## Relationship to Existing Code

MolSysViewer already hinted at labels before the first annotation slice was
implemented.

Historical evidence:

- `clear_decorations(..., labels=True)` existed in Python
- JS had a `clearLabels` placeholder
- some shapes accepted label-like payloads locally

Current first implemented slice:

- `view.annotations` now exists in Python
- `view.annotations.add_label(...)` creates a persistent label anchored to one `group`
- labels are replay-safe, rebuild-safe, and export-safe through annotation history replay
- labels are layer-aware from the start (`kind="annotation"`)
- `clear_decorations(..., labels=True)` now clears real frontend labels
- compact strip overlays for group labels now exist
- strip label overlays can seed `annotation` context targets
- strip label overlays can also seed a first narrow `annotation` slice in `active_selection`
- `element + annotation` can now coexist in one mixed selection payload
- `shape` and broader mixed-selection semantics remain later work

So this work is not inventing an unrelated abstraction.
It is closing a category gap that the codebase already suggested.

## Alternatives Considered

### 1. Treat labels as shapes

Not chosen.

Why:

- conflates semantic text with geometry overlays,
- makes future context/selection logic muddier,
- weakens taxonomy clarity.

### 2. Keep labels as one-off special cases only

Not chosen.

Why:

- would not scale to persistent labels as a product feature,
- would keep `clear labels` and export semantics ad hoc,
- would not support future annotation families.

### 3. Introduce `annotations`

Chosen direction.

Why:

- matches the product direction,
- aligns with Mol* precedents,
- keeps the viewer taxonomy clean,
- supports future growth without overloading `shapes`.

## Future Growth

Plausible growth after the first label slice:

- shape-attached labels
- explicit point labels
- richer annotation types beyond labels
- annotation overlays on `GroupStrip`
- annotation-aware context menus
- annotation participation in `active_selection`
- annotation-driven tooltips or inspector panels

Current narrowing decision:

- annotation-aware context begins from `GroupStrip` overlay badges before canvas label pickability
- this gives `annotation` a real `context_target` path without yet depending on Mol* label picking semantics
- canvas-side annotation pickability remains a later step

`GroupStrip` alignment note:

- labels are not first-class strip items in `GroupStrip` v1
- future strip integration should happen as overlays or marks, not by changing the strip's primary element model

## Immediate Implication for Development

Before implementing labels, keep these rules intact:

- do not add persistent labels under `shapes`
- keep annotation semantics separate from hover tooltips
- keep annotations layer-aware
- keep annotation tags deterministic and replay-safe
- keep labels safe across replay, rebuild, and export
- keep the first annotation slice narrow and replay-safe

## Technical Pattern Worth Borrowing From Mol*

Mol* suggests a useful implementation pattern even if we do not copy its UI or
representation layer wholesale:

- use text-specific rendering/building primitives rather than pretending labels are ordinary meshes
- keep label content separate from label placement
- derive placement from element-anchored bounds/centers when possible

For MolSysViewer, the strongest immediate technical lesson is:

- labels should likely be built from element-derived anchor data, not improvised ad hoc geometry payloads
