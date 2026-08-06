# Canvas panel taxonomy, as proposed in April 2026

**ARCHIVED 2026-08-06. This is the panel model MolSysViewer did *not* build.**

`canvas_minimal_ux.md` proposed organising the panel surface around two panels,
`Navigate` and `Workbench`, and specified their internal sections and layout in
detail. What shipped instead is **Studio + Add-ons**, with ten Studio subpanels
(System, Whole, Selections, Regions, Annotations, Measures, Shapes, Layers,
Viewport, Export) navigated by tabs.

It is kept because the reasoning is still worth reading — the "map side vs
inventory side" distinction, the argument for list-like rather than editor-like
panels, and the navigator alternatives — and because `canvas_minimal_ux.md`'s own
Documentation Rule asks that resolved questions be *moved out*, not deleted.

Read it as history. Nothing here describes current behaviour.

---

## Candidate Panel Taxonomy

The current preferred simplification is to organize visual panel UX around:

- `Navigate`
- `Workbench`

### `Navigate`

Handles:

- group hierarchy
- structural navigation
- active target discovery
- saved selections
- regions

Current design note:

- `regions` sit close to navigation because they still answer "what part of the
  system am I working on?"
- even though they are also persistent workbench objects

This is the "map" side.

### `Workbench`

Handles:

- annotations
- measurements
- shapes
- scene styles / presets

Current design note:

- this panel should gather the scene artifacts and scene-facing state without
  forcing the user to learn many separate visual panels

This is the "inventory / artifact" side.

This two-panel direction is preferred because it keeps the visual model small
while still allowing a rich programmatic API behind it.

## First Content Distillation For The Two Panels

The first implementation should favor lightweight list-based panels, not dense
editor-like panels.

The panel system should initially feel more like:

- a clean workbench navigator
- a light inventory of persistent objects

and less like:

- a dashboard
- a property inspector full of controls
- a mini application embedded over the canvas

### `Navigate`: First Internal Sections

Current preferred sections:

- `Structure`
- `Active`
- `Saved`
- `Regions`

#### `Structure`

Purpose:

- locate the relevant part of the molecular system quickly

Preferred contents:

- visible structural hierarchy
- enough hierarchy to move through:
  - group
  - component
  - molecule
  - chain

Important rule:

- this should feel like a map
- not like a metadata inspector
- in practice this should be the dominant block inside `Navigate`

#### `Active`

Purpose:

- expose the current live working target

Preferred contents:

- current `active_selection`
- a compact summary only
- a very small number of actions, such as:
  - save
  - convert to region
  - clear

Important rule:

- if nothing is active, this section should stay visually very small

#### `Saved`

Purpose:

- bring back previously saved structural targets

Preferred contents:

- short list of saved selections
- each row should stay lightweight

Preferred row behavior:

- click restores the saved selection into `active_selection`
- secondary actions live in row context menu

#### `Regions`

Purpose:

- manage persistent structural areas of interest

Preferred contents:

- short list of persistent regions

Preferred row behavior:

- click activates the region as current object of work
- one small visible affordance may control visibility
- richer actions remain contextual

Current design note:

- `Saved` and `Regions` are intentionally kept here for now because they still
  answer "what part of the system am I working on?"

### `Navigate`: First Layout Direction

The first preferred layout is:

- one single vertical column
- sections stacked in this order:
  1. `Structure`
  2. `Active`
  3. `Saved`
  4. `Regions`

This order is intentional:

- first locate the system target
- then inspect the current active target
- then recover saved targets
- then manage persistent structural areas of interest

First space-distribution direction:

- `Structure`:
  - dominant block
  - roughly `45-55%` of the useful vertical space
- `Active`:
  - compact block
  - roughly `10-15%`
- `Saved`:
  - medium block
  - roughly `15-20%`
- `Regions`:
  - medium block
  - roughly `15-20%`

Important rule:

- `Structure` should absorb most navigational density
- the rest of `Navigate` should stay compact and calm

### `Workbench`: First Internal Sections

Current preferred sections:

- `Annotations`
- `Measurements`
- `Shapes`
- `Scene`

#### `Annotations`

Purpose:

- manage persistent labels/annotations already placed into the scene

Preferred contents:

- concise list of annotation records
- emphasis on identification and activation, not on deep inline editing

Preferred row behavior:

- click activates the annotation
- one small visible affordance may control visibility
- richer actions remain contextual

#### `Measurements`

Purpose:

- manage persistent measurements as workbench objects

Preferred contents:

- concise list of measurements
- each row should show only the most important summary, such as:
  - measure type
  - main value

Preferred row behavior:

- click activates the measurement
- one small visible affordance may control visibility
- richer actions remain contextual

#### `Shapes`

Purpose:

- manage persistent scene shapes without turning the panel into a shape editor

Preferred contents:

- concise list of tagged shapes
- minimal summary per row

Preferred row behavior:

- click activates the shape/object
- one small visible affordance may control visibility when relevant
- type-specific operations stay contextual

#### `Scene`

Purpose:

- expose a very small amount of scene-level visual state

Preferred contents:

- current scene style/preset
- canonical scene-style shortcuts
- later, possibly a very small number of global scene utilities

Important rule:

- this should not become a crowded settings panel
- keep it very short and highly curated

### `Workbench`: First Layout Direction

The first preferred layout is:

- one single vertical column
- sections stacked in this order:
  1. `Annotations`
  2. `Measurements`
  3. `Shapes`
  4. `Scene`

This order is intentional:

- start with the most directly scientific persistent artifacts
- continue with other persistent visual objects
- finish with the small scene-level state area

First space-distribution direction:

- `Annotations`:
  - medium block
  - roughly `25-30%`
- `Measurements`:
  - medium block
  - roughly `25-30%`
- `Shapes`:
  - small-to-medium block
  - roughly `15-20%`
- `Scene`:
  - small curated block
  - roughly `15-20%`

Important rule:

- `Workbench` should feel like a calm inventory
- it should not feel like a control room or settings dashboard


## Panel Navigation Variants

Two panel-navigation variants are currently worth keeping alive in design:

- tabs
- discreet carousel

### Tabs

This is the current recommended first implementation direction.

Why:

- fastest
- lowest friction
- least likely to frustrate repeated users
- easiest to validate

Important rule:

- tabs should belong to panel mode
- they should not become permanent canvas chrome in the resting state
- tabs are the preferred first implementation not because they are prettier,
  but because they are most likely to minimize friction and fatigue

### Discreet Carousel

This remains a valid future or configurable alternative.

Useful qualities:

- stronger product personality
- spatial clarity if kept very restrained
- one clear active panel with neighboring panels merely suggested

Important rule:

- do not copy Coverflow/Shift effects literally
- keep motion short and restrained
- prioritize comfort over spectacle
- treat it as a later/configurable navigator, not as the first system that the
  whole panel architecture depends on

