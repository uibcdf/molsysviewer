# Style Battery And Future Ideas

This page defines the recommended first battery of styles/presets for
MolSysViewer and records useful future ideas inspired by Mol* and nglview.

Its purpose is to keep style growth intentional.

MolSysViewer should not accumulate a large number of vague visual options.
It should offer a small, memorable, scientifically useful battery first.

## What We Learned From Nearby Tools

### From Mol*

Mol* makes a useful distinction between:

- representation presets
  - what structural representations are built
- styles
  - how those representations and the scene look visually

This distinction is healthy and should be preserved in MolSysViewer.

Useful references reviewed:

- `representation-preset.ts`
- `quick-styles.tsx`

### From nglview

nglview is valuable in a different way.

It emphasizes:

- a simple user-facing API
- direct representation control
- compact recipes and shortcuts

Useful lesson:

- users value a short path from intent to result
- but MolSysViewer should still keep a stronger semantic layer than a raw
  list of representations

## Targeting Rule

MolSysViewer should not mix up two different questions:

- what part of the system is being addressed
- how that part should look

The first question belongs primarily to MolSysMT selection semantics.
The second belongs to MolSysViewer visual semantics.

So the long-term contract should be:

- MolSysMT defines targets
- MolSysViewer defines style

This means future style growth should prefer:

- `whole`
- `regions`
- `active_selection`
- persistent selections
- or APIs that accept MolSysMT-compatible `selection=...`

and should avoid:

- inventing a separate style-target mini-language
- burying structural predicates inside opaque visual presets
- creating style objects that cannot be traced back to a structural target

## Product Rule

The first style battery should be:

- small
- explicit
- reproducible
- easy to remember
- scientifically meaningful

Do not optimize for option count.

Optimize for:

- clarity
- stability
- and usefulness in real structural work

## Taxonomy Rule

For design work, it is acceptable and useful to think with more concepts than
the final user-facing API may expose.

So for now it is healthy to distinguish:

- `preset`
- `style`
- `look`
- `focus style`

because each one answers a different question.

But the public product surface should remain conservative.

If real usage shows that users work more comfortably with a compact mental
model, MolSysViewer should prefer:

- keeping the richer taxonomy in the design documents
- and compacting the public API around `Style` where possible

## First Recommended Battery

The first battery should combine:

- a few structural scene recipes
- and a very small number of visual scene styles

This does **not** mean all of them need to be implemented immediately.
It means these are the canonical targets the project should organize around.

## Canonical Scene Recipes

### 1. `default`

- kind: `scene`
- role: neutral baseline
- intent: let MolSysViewer choose the sensible default scene
- current backing: existing `preset="auto"`
- status: already effectively available through the current preset base

### 2. `polymer-cartoon`

- kind: `scene`
- role: structural overview
- intent: show the macromolecular fold clearly
- current backing: existing `preset="polymer-cartoon"`
- status: already effectively available through the current preset base

### 3. `polymer-and-ligand`

- kind: `scene`
- role: protein-ligand inspection baseline
- intent: show polymers clearly while keeping ligand detail visible
- current backing: existing `preset="polymer-and-ligand"`
- status: already effectively available through the current preset base

### 4. `atomic-detail`

- kind: `scene`
- role: local chemistry inspection
- intent: show atomistic detail for small or focused systems
- current backing: existing `preset="atomic-detail"`
- status: already effectively available through the current preset base

### 5. `coarse-surface`

- kind: `scene`
- role: large-system overview
- intent: give an interpretable coarse envelope for large systems
- current backing: existing `preset="coarse-surface"`
- status: already effectively available through the current preset base

### 6. `empty`

- kind: `scene`
- role: explicit blank baseline
- intent: make room for controlled additive artifacts or later focused display
- current backing: existing `preset="empty"`
- status: already effectively available through the current preset base

## Canonical Visual Scene Styles

These are not yet a separate runtime layer in MolSysViewer, but they are
valuable targets for the future style system.

### 7. `default-look`

- kind: `scene-style`
- role: neutral visual appearance
- intent: standard lighting/material baseline
- inspiration: Mol* quick style `default`
- current backing: not yet separate from current scene defaults
- status: future
- implementation note: should be treated as a future scene-look layer, not as
  another structural recipe

### 8. `illustrative`

- kind: `scene-style`
- role: communication/publication emphasis
- intent: stronger outlines, more readable shape separation, more stylized scene
- inspiration: Mol* quick style `illustrative`
- current backing: not yet a first-class MolSysViewer style
- status: future
- implementation note: should be treated as a future scene-look layer, not as
  another structural recipe

## Recommended Public Naming Strategy

For the first public battery, prefer names that communicate purpose.

Good examples:

- `polymer-cartoon`
- `polymer-and-ligand`
- `atomic-detail`
- `illustrative`

Avoid:

- vague names
- internal-engine jargon
- names that hide whether something is structural or purely visual

## Recommended Near-Term Mapping

Near term, MolSysViewer should expose these scene recipes through `Style`
without pretending they are already independent runtime families.

So the current mapping should stay:

- scene recipe name
  -> `Style(preset=...)`

Only later should MolSysViewer promote some of these into richer style objects
that also carry:

- visual look
- postprocessing
- color rules
- scene-wide options

## What Should Come Soon

These are the next healthy style-facing steps:

1. keep the first battery small and canonical
2. document the recommended scene recipes clearly
3. support them in:
   - scripts/notebooks
   - style registry
   - `_molsysviewer.py`
4. keep canvas interaction limited to applying or previewing these recipes

## Future Ideas Worth Tracking

These ideas are useful, but they should remain future-facing until the core
style contract is stronger.

### Focus Styles

Inspired by the product vision:

- make the current selection stand out
- desaturate or soften the rest
- define a reusable "inspection focus" layer

This should become the next major style family **after** scene styles are
stable.

When that happens, focus styles should still follow the targeting rule above:

- the focus target should come from MolSysMT-compatible selection semantics or
  stable MolSysViewer selection objects
- the focus style should only define the visual treatment applied to that
  target

### Publication Styles

Potential future recipes:

- `publication`
- `presentation`
- `figure-clean`

These should not be arbitrary aesthetic presets.
They should correspond to stable visual narratives for scientific
communication.

### Analysis-Oriented Styles

Potential future recipes:

- `binding-site`
- `interface`
- `trajectory-review`
- `charge-surface`
- `hydrophobicity`

These are valuable, but only if they tie clearly to:

- actual scientific data
- reproducible state
- and explicit semantics

### Style Application In Canvas

Future canvas affordances should likely begin with:

- apply a registered style
- preview a registered style
- revert or confirm

Only much later:

- author or edit styles in the canvas

Even then, the canvas should not become the owner of structural targeting
syntax. It may help users pick targets interactively, but persistent target
state should still map back to MolSysMT-compatible semantics.

### Project-Level Style Libraries

The `_molsysviewer.py` mechanism may later support:

- a project-wide style catalog
- stable default scene style
- reusable organization-specific visual standards

This is especially valuable if MolSysViewer is embedded by another scientific
library.

### Exportable Style Specs

Future direction:

- JSON/YAML export of named styles
- portable style packs
- reproducible visual standards shared across projects

This should remain future work until the Python-side style object is more
mature.

## What To Avoid

Do not do these too early:

- a large uncurated style catalog
- canvas-only style definitions
- many overlapping names for nearly identical recipes
- style concepts that duplicate raw representation arguments without adding
  semantic value
- style machinery that becomes more complex than the actual scientific use

## Operational Recommendation

For now, MolSysViewer should offer a **curated battery**, not an encyclopedic
one.

Keep the first memorable set centered on:

- `default`
- `polymer-cartoon`
- `polymer-and-ligand`
- `atomic-detail`
- `coarse-surface`
- `empty`

And keep these visible as the first visual-style targets:

- `default-look`
- `illustrative`

## Short Rule

Keep this rule visible:

> A good style battery is not large. It is memorable, reproducible, and useful
> for real scientific work.
