# Canvas Minimal UX

This page records the current design direction for the visual and interaction
surface of the MolSysViewer canvas and popup.

Its purpose is to prevent drift toward noisy, menu-heavy, toolbar-heavy UI.

## Core Principle

The canvas should remain as visually quiet as possible.

In the resting state, the user should ideally see:

- the molecular system
- the trajectory scrubber, but only when a trajectory is actually present
- a very small set of meta-controls

The canvas should not feel like a dashboard.

## Two Main Interaction Doors

The current preferred interaction model for non-programmatic use is:

1. right click
2. panel mode

This means:

- the context menu is the primary entrypoint for immediate, target-scoped actions
- panel mode is the primary entrypoint for deeper navigation and persistent workbench interaction
- the canvas should not grow extra always-visible interaction systems unless they are clearly superior to these two doors

The product should resist adding many other permanent UI doors unless a very
strong reason appears.

## Resting Canvas

The resting canvas should aim for:

- molecule first
- UI second
- clean negative space
- as little persistent chrome as possible

The trajectory scrubber is an intentional exception:

- if more than one structure/frame exists, the scrubber is justified as part of the data interaction
- if not, it should not appear

This exception is important:

- the scrubber is a data navigation control, not merely decorative UI
- therefore it can remain visible without violating the minimal-canvas goal

## Permanent Canvas Controls

The current preferred minimum permanent controls are only:

- open/close panel mode
- fullscreen
- popup

These controls are above the scientific scene.
They are viewer-container controls, not scene-manipulation controls.

This is why they deserve different treatment from scene actions such as:

- background toggle
- spin
- swing
- scene-style changes

Those scene actions should live instead in:

- the context menu
- panel mode
- or both

Current examples of scene-facing actions that should not remain as permanent
canvas buttons:

- background toggle
- spin
- swing
- reset-camera style actions

## Visual Language For The Three Permanent Controls

The controls should be:

- minimal
- elegant
- low-noise
- consistent in stroke/weight
- grouped discretely

Preferred icon direction:

- panel mode
  - a minimal panel-like rectangle or frame, not a generic hamburger menu
- fullscreen
  - four outward expansion arrows / corners
- popup
  - diagonal outward arrow with corner

These should read as meta-controls for the viewer shell, not as scientific tools.

Placement direction:

- keep them grouped very discreetly
- avoid a toolbar look
- prefer a very small control cluster over scattered buttons
- keep the panel control slightly more legible than the other two if needed,
  because it is the main structured workspace door

### Preferred Cluster Direction

The current preferred direction is:

- one small horizontal cluster
- likely placed at the upper-right area of the canvas
- `panel`, then `fullscreen`, then `popup`

Reason:

- it keeps the permanent controls together
- it avoids scattered chrome
- it makes the main workspace door appear first

This cluster should feel like a very light shell utility, not like a toolbar.

### Preferred Weight And Size

The three controls should stay visually light.

Preferred direction:

- small icons
- fine, consistent strokes
- low visual weight in resting state
- click target larger than the visible icon
- modest spacing between icons

Important rule:

- optimize for discoverability without turning the cluster into a strong visual
  object
- the user should notice the controls when needed, not be constantly reminded
  of them

### First State Direction

Preferred common states:

- resting:
  - lowest contrast
  - no heavy fill
- hover:
  - slightly more legible
  - may gain a very small local background or contrast lift
- active:
  - only when the control has a meaningful persistent active state

Important rule:

- all three controls should share one family of hover/rest behavior
- do not give each control a different visual language

### `panel`

Role:

- main structured workspace door

Preferred icon:

- a minimal panel-like rectangle or frame
- not a hamburger menu

Preferred behavior:

- click toggles panel mode open/closed
- should reflect open/closed state visually
- may be slightly more legible than the other two controls

Important rule:

- this is the one permanent control that should most clearly indicate state,
  because it opens the workbench surface itself

### `fullscreen`

Role:

- viewer-shell expansion

Preferred icon:

- four outward corners or expansion marks

Preferred behavior:

- click toggles fullscreen mode
- may reflect active fullscreen state subtly

Important rule:

- keep the active state restrained; fullscreen is useful, but should not
  visually dominate the cluster

### `popup`

Role:

- open the viewer in a separate popup window

Preferred icon:

- diagonal outward arrow with corner

Preferred behavior:

- click opens or transfers to popup behavior according to the runtime context
- does not need a heavy persistent active state unless a real usability need
  appears

Important rule:

- avoid over-signaling popup state if doing so adds visual noise without clear
  user value

## Panel Mode

Panel mode is the single structured workspace entrypoint beyond the context
menu.

Panel mode should:

- be invokable through one consistent mechanism
- likely be reachable by both:
  - a keyboard shortcut
  - one small canvas button
- show one main panel at a time
- disappear fully when closed
- remember the last active panel
- work the same way in notebook canvas and popup canvas

The user should not be forced to look at panels all the time.

The panel-switching mechanism and the panel-content mechanism should be treated
as separate concerns:

- one shared panel mode
- one shared panel-content registry
- one swappable navigator

This should also stay compatible with optional ecosystem add-ons:

- the built-in target remains `Navigate` + `Workbench`
- but the panel-mode architecture should not assume there can only ever be two
  panels
- optional MolSysSuite add-ons should normally surface themselves through this
  same panel-mode system, not through new permanent canvas chrome

Future host-layout note:

- the canonical experience is still one canvas host with panel mode inside it
- but a future standalone or popup-based advanced mode may allow panel mode to
  live in an auxiliary window on a second screen while the main canvas remains
  alone in the primary window
- if that ever happens, it should be treated as an optional host layout, not as
  a replacement for the canonical minimal single-window model

Current practical bridge state:

- the runtime still has only one real panel implementation:
  - `GroupPanel`
- the runtime now has two real panel implementations:
  - `GroupPanel`
  - `WorkbenchPanel`
- both are still drawer-like, not yet the final centered floating `panel mode`
- but it has now taken a first structural step toward the future model:
  - reusable shell chrome
  - explicit `Navigate` identity
  - explicit `Workbench` identity
  - cleaner separation between panel chrome and panel content
  - `Navigate` now also exposes first lightweight live sections below `Structure`:
    - `Active`
    - `Saved`
    - `Regions`
  - `Navigate` now also has its first lightweight row actions:
    - click `Saved` -> restore `active_selection`
    - click `Regions` -> focus region
  - real `Workbench` sections and empty states already scaffolded
  - minimal controller wiring for `Workbench` rows based on live runtime summaries
  - first row-level primary action already present when structural anchoring is available:
    - click row -> focus target
  - `Workbench` rows now also expose first local visual states:
    - `active`
    - `context` for tagged annotations/shapes while the menu is open
  - `Workbench` rows now also expose a first minimal persistent affordance:
    - per-row visibility toggle for tagged annotations, measurements, and shapes
  - `Workbench` sections can now collapse/expand locally
  - the drawer runtime now also exposes a first shared panel navigator in the
    header chrome:
    - current panel shown as the active pill
    - sibling panel shown as the secondary jump target
    - direct `Navigate <-> Workbench` switching already works before the final
      shared floating container and formal `tabs`

## First Container Direction For Panel Mode

The current preferred panel-mode container is:

- one floating panel
- centered vertically
- centered horizontally
- rounded corners
- visually light, not heavy or window-like
- neutral translucent background

The point is to feel like a temporary work surface over the canvas, not like a
permanent sidebar and not like a dense application window.

### Preferred Container Rule

Both `Navigate` and `Workbench` should initially share the same base
container.

Reason:

- visual stability
- one clear mental model of panel mode
- switching panel should feel like changing workspace content, not opening a
  different window system

### Preferred Size Direction

The first working size direction is approximately:

- width:
  - about `68-74%` of the canvas
- height:
  - about `62-72%` of the canvas

Current mental center:

- around `72%` width
- around `68%` height

This is intentionally large enough for calm reading and navigation, but still
small enough to leave visible molecular context around the panel.

### Internal Container Structure

The preferred first internal structure is:

- a very small header
- one main body area
- no footer by default

Header:

- should stay visually compact
- should host the panel title and/or navigator
- should not become a toolbar

Body:

- should contain the real panel content
- should carry the scroll behavior
- should have enough internal spacing to prevent density and fatigue

## Panel Mode Open/Close Behavior

Panel mode should feel easy to enter and easy to leave.

Current preferred behavior:

- the same panel button that opens panel mode should also close it
- the same keyboard shortcut that opens panel mode should also close it
- `Esc` should also be treated as a likely close path
- the first shared runtime API can already be expressed as:
  - `set_panel_mode(panel="navigate"|"workbench"|None, expanded=True|False)`

Current caution:

- do not rely on only one close mechanism
- leaving panel mode should feel immediate and unsurprising

Still-open question:

- whether clicking outside the floating panel should close panel mode
- this should be decided by prototyping, because it affects both speed and
  accidental closure risk

## Panel And Canvas Relationship While Open

While panel mode is open, the panel should be the primary interaction surface,
but the molecular scene should still remain visually present.

Current preferred direction:

- the panel comes to the front clearly
- the canvas remains visible behind it
- the panel should not feel like a hard full-screen modal takeover

Current caution:

- avoid making the background scene so visually strong that the panel loses
  clarity
- avoid dimming the scene so much that panel mode feels disconnected from the
  molecular context

Still-open question:

- whether the background canvas should remain partially interactive while panel
  mode is open, or whether interaction should be effectively captured by the
  panel until it closes

## Scroll Rules

The first panel version should avoid complicated nested scrolling whenever
possible.

Current preferred direction:

- the main body area can scroll
- sections should remain visually stable and simple
- if one section clearly carries most density, it may absorb most of the
  practical scrolling pressure

Current design note:

- `Navigate/Structure` is the most likely candidate for the densest internal
  navigation area
- therefore it may eventually deserve special scroll treatment if prototyping
  proves that necessary

Important rule:

- do not introduce many independently scrolling mini-panels unless clearly
  justified
- too many scroll containers will increase fatigue and confusion

## Empty State Rules

Empty states should stay visually light.

Current preferred direction:

- an empty section should occupy very little space
- empty sections should not create large dead boxes
- short, quiet messages are acceptable if they help orientation

Examples:

- empty `Active`
  - should stay minimal rather than reserving a large placeholder area
- empty `Saved`, `Regions`, `Annotations`, `Measurements`, or `Shapes`
  - may show a short line of guidance or simply remain compact

Important rule:

- empty state treatment should preserve the feeling of calm and negative space
- the panel should not look unfinished or noisy just because several sections
  are currently empty

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

## First Row Pattern For List-Based Panels

The first panel version should prefer a common, minimal row pattern across
`Saved`, `Regions`, `Annotations`, `Measurements`, and `Shapes`.

Preferred row structure:

- short title
- optional very short secondary line
- one stable state marker
- one primary click action
- at most one small visible secondary affordance
- richer actions in row context menu

Important rules:

- do not place many small buttons in every row
- do not force dense editing controls into list rows
- empty sections should collapse gracefully and occupy very little space
- the first panel version should feel like a reader/organizer, not like a
  full editor

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

## Configuration Direction

If multiple navigation variants are ever exposed, the healthy layering should be:

- one common panel mode
- one common panel registry/content model
- one swappable panel navigator

For example:

- `tabs`
- `carousel`

The product should avoid maintaining two unrelated panel systems.

Healthy implementation order:

1. define one common panel mode
2. implement `tabs`
3. keep the navigator boundary clean
4. explore `carousel` later as an alternative/configurable navigator

The public configuration, if it exists, should switch only the navigator, not
the underlying panel model.

## Context Menu Role

The context menu should absorb many actions that do not justify permanent
canvas controls.

Important examples include:

- background
- spin
- swing
- reset/view utility actions

The empty-canvas context menu is especially useful for these scene-level
actions because they are above any one structural target but still belong to
the current viewing session.

Current caution:

- avoid duplicating too many of these scene/session actions in both panel mode
  and the context menu unless there is a clear usability reason
- the system should not slowly regrow multiple overlapping doors for the same
  operation

## State Hierarchy For Panel And Canvas

The visual state language should stay very small.

Current preferred state hierarchy:

1. `hidden`
2. `hover`
3. `context`
4. `active`

This hierarchy is intentionally narrow.
Avoid adding more visible states unless a concrete workflow proves they are
needed.

### `hidden`

Meaning:

- the object still exists
- but it should not compete for current attention

Preferred treatment:

- in panels:
  - attenuated row
  - visibility toggle shown as off
  - text still readable
- in canvas:
  - absent or visually suppressed according to the object semantics

### `hover`

Meaning:

- the user is only inspecting the object momentarily

Preferred treatment:

- in panels:
  - very light transient highlight
- in canvas:
  - minimal temporary emphasis if applicable

Important rule:

- `hover` must not look like stable selection or working context

### `context`

Meaning:

- the object is the target of the current context menu or context-scoped action

Preferred treatment:

- in panels:
  - a discrete but clear context marker
- in canvas:
  - a restrained contextual emphasis

Important rule:

- `context` is stronger than `hover`
- `context` should still remain lighter than `active`

### `active`

Meaning:

- this is the current object of work

Preferred treatment:

- in panels:
  - the clearest stable row marker
- in canvas:
  - a stable but sober emphasis

Important rule:

- `active` should be unmistakable
- but it should not become loud or visually tiring

## State Priority Rules

If multiple states overlap, the preferred priority is:

- `active` over `context`
- `context` over `hover`
- `hidden` modulates the overall appearance underneath the other states

This means:

- an object can remain active while also being hovered, but it should still
  read primarily as active
- an object can be context-targeted while hidden in the current visual scene,
  but the hidden state should still attenuate it overall

## Activation Semantics

The panel interaction model should distinguish activation from focus.

Current preferred rule:

- click should usually activate
- focus should usually remain an explicit secondary action

Reason:

- focus moves the camera and is more intrusive
- activation is safer, calmer, and better suited to repeated work

### What `active` Should Mean By Category

- saved selection
  - restore its contents into `active_selection`
- region
  - make that region the current region of work
- annotation
  - make that annotation the current annotation of work
- measurement
  - make that measurement the current measurement of work
- shape
  - make that shape the current shape/object of work

### What Activation Should Not Do By Default

- it should not focus the camera automatically
- it should not show-only automatically
- it should not open an editor automatically
- it should not trigger destructive actions

## Shared Interaction Grammar For Panel Rows

The panel lists should reuse one calm, repeated grammar whenever possible:

- click:
  - activate the item
- one small visible affordance:
  - usually visibility, when that concept applies
- right click:
  - open item-specific secondary actions

The goal is that the user learns one interaction language and can then use all
panel lists without extra explanation.

## First Per-Category Row Actions

The first implementation should keep row actions extremely small.

### `Saved`

- click:
  - restore the saved selection into `active_selection`
- visible secondary affordance:
  - usually none in the first pass
- contextual actions:
  - rename
  - delete
  - convert into region

### `Regions`

- click:
  - activate the region as the current object of work
- visible secondary affordance:
  - visibility toggle
- contextual actions:
  - rename
  - focus
  - show only
  - delete

### `Annotations`

- click:
  - activate the annotation as the current object of work
- visible secondary affordance:
  - visibility toggle
- contextual actions:
  - edit
  - reanchor
  - delete

### `Measurements`

- click:
  - activate the measurement as the current object of work
- visible secondary affordance:
  - visibility toggle
- contextual actions:
  - focus
  - delete
  - possibly copy value later if it proves useful

### `Shapes`

- click:
  - activate the shape/object as the current object of work
- visible secondary affordance:
  - visibility toggle when relevant
- contextual actions:
  - rename
  - delete
  - type-specific actions if justified later

Important rule:

- do not try to expose all management operations inline
- use the context menu to keep rows visually calm

## What To Avoid

The canvas should resist drifting toward:

- many permanent buttons
- multi-row toolbars
- dense floating menus
- several panels visible at once by default
- a webapp dashboard look
- decorative motion that slows frequent actions

## Working Summary

The current working UX target is:

- clean canvas
- trajectory scrubber only when needed
- only three permanent meta-controls:
  - panel
  - fullscreen
  - popup
- right-click context menu for immediate actions
- panel mode for deeper navigation and workbench interaction
- same panel model in canvas and popup
- `Navigate` + `Workbench` as the current preferred visual simplification
- `tabs` first
- `carousel` later or configurable

## Closed Decisions So Far

The following points should be treated as currently decided unless later
prototyping shows a strong reason to change them:

- the canvas resting state should stay visually quiet
- the molecular scene is the primary visual subject
- the trajectory scrubber is the only justified always-visible data control,
  and only when trajectory/frame navigation is actually present
- the two main interaction doors for non-programmatic use are:
  - right-click context menu
  - panel mode
- only three permanent viewer-shell controls should remain on the canvas:
  - panel
  - fullscreen
  - popup
- scene-facing actions such as `background`, `spin`, `swing`, and similar
  view-utility actions should leave the permanent button area
- panel mode should show one main panel at a time and disappear fully when
  closed
- the same conceptual panel model should work in notebook canvas and popup
- the first panel-navigation implementation should be `tabs`
- the current preferred panel simplification is:
  - `Navigate`
  - `Workbench`

## Open Questions To Preserve

These questions are intentionally still open. Keep them visible so they are not
forgotten during implementation.

- exact placement of the three permanent meta-controls
  - likely as one very small cluster
  - still to decide whether the panel control should be slightly separated
- exact visual states of those controls
  - especially whether `panel` should visibly reflect open/closed state
- exact access gesture for panel mode
  - keyboard shortcut only is not enough
  - a small canvas button is likely needed
  - the final shortcut key still needs to be chosen
- exact visual treatment of the already chosen sections inside `Navigate`
  - section headers
  - collapse behavior
  - spacing and density
- exact visual treatment of the already chosen sections inside `Workbench`
  - section headers
  - collapse behavior
  - spacing and density
- whether the `Navigate` + `Workbench` split is sufficient in practice or
  whether one domain needs to break out later
- whether some items should migrate between `Navigate` and `Workbench` after
  prototyping, especially:
  - `regions`
  - saved selections
  - styles/presets
- what scene-level actions should appear only in the empty-canvas context menu
  versus also being exposed inside `Workbench`
- whether `fullscreen` and `popup` should also appear in the context menu as
  duplicates, or remain only as permanent shell controls
- whether the popup should use exactly the same permanent control cluster as
  the notebook canvas, or a slightly reduced one

## Candidate Options Still Worth Keeping Alive

The following alternatives are still worth preserving in the guide even though
they are not the current first implementation target.

### Panel Navigator Options

- `tabs`
  - preferred first implementation because it is likely the fastest and least
    fatiguing
- discreet `carousel`
  - still considered viable as a future/configurable navigator
  - should reuse the same panel mode and panel content model
  - should not introduce a second panel architecture

### Panel Taxonomy Options

- current preferred simplification:
  - `Navigate`
  - `Workbench`
- still worth re-evaluating later if prototyping shows the two-panel model is
  too compressed:
  - a more split panel taxonomy, for example separating navigation from
    artifact-management domains such as annotations or measurements

### Panel Access / Selection Options

- a small permanent panel button plus keyboard shortcut
- `tabs` as the first concrete navigator
- later, a discreet switcher inspired by carousel / coverflow / shift-style
  navigation, but stripped down for comfort and speed rather than spectacle

## Deferred Decisions

These are not blocked conceptually, but they should be decided later rather
than guessed too early.

- exact icon drawing and stroke language for the three permanent controls
- whether the panel switcher needs transition animation beyond a very small
  functional motion
- whether the user should eventually be able to choose navigator mode through
  configuration
- whether panel mode should remember only the last active panel or also some
  panel-local scroll/section state
- whether the popup should expose a reduced `Workbench` subset or the full
  panel set

## Documentation Rule

When this UX direction evolves, update this file by preserving three separate
layers:

- what is already decided
- what options are still intentionally alive
- what questions remain open

This file should not present only the current favorite. It should also retain
the relevant alternatives and unresolved decisions so they are not rediscovered
from scratch in later sessions.

When a question is resolved, move it out of the open-question sections rather
than silently replacing the surrounding text. The point of this page is to
preserve both direction and memory.
