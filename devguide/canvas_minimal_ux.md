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

Minimal, elegant and low-noise, consistent in stroke and weight, grouped
discreetly. They should read as meta-controls for the viewer shell, not as
scientific tools — so no toolbar look, and a very small cluster rather than
scattered buttons.

Icons: a minimal panel-like rectangle for panel mode (not a generic hamburger),
four outward corners for fullscreen, a diagonal outward arrow for popup. The
panel control may be slightly more legible than the other two, since it is the
main workspace door.

### Preferred Cluster Direction

One small horizontal cluster, likely upper-right: `panel`, then `fullscreen`,
then `popup`. That keeps the permanent controls together, avoids scattered
chrome, and puts the main workspace door first. It should feel like a light
shell utility.

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

Current runtime direction:

- the workspace overview should keep moving toward a
  light mosaic language
- the current workspace card may act as a small "hero" summary of the active
  host:
  - active panel
  - entry
  - capability hints
  - first dynamic section previews
- non-current workspace cards may still expose compact capability chips when
  that helps the user understand that an add-on workspace is substantive and
  not just a label
- when those chips exist, they should summarize real runtime affordances:
  - local panels
  - workbench sections
  - context actions
  - export helpers
- non-current workspace cards may also preview one or two real section titles
  when that helps communicate domain structure without turning the overview into
  a dashboard
- the current workspace card may also expose a compact local panel lane when
  that helps tie the overview to the host below:
  - current panel title
  - current panel description
  - current panel entry
  - direct panel switching
- the active workspace host should remain visually tied to that overview rather
  than feeling like an unrelated second card
- this is still meant to feel like calm navigation, not like a dashboard or a
  second toolbar

The shared header should reinforce the same reading:

- workspace switching should feel like switching domains of work
- the trigger should communicate at least:
  - current workspace title
  - current workspace subtitle when useful
  - whether the user is in `Core` or an add-on workspace

This should also stay compatible with optional ecosystem add-ons:

- the built-in target remains the Studio and Add-ons panels
- but the panel-mode architecture should not assume there can only ever be two
  panels forever

## Workspace Launcher Direction

The workspace selector should now be read as evolving toward a small domain
launcher rather than a plain dropdown.

Near-term direction:

- keep the selector in the shared header
- preserve one current workspace trigger
- but let the opened launcher read more like a small card grid when several
  workspaces exist

Reason:

- a flat list is still acceptable for two workspaces
- it becomes weak once several ecosystem workspaces coexist
- a light launcher grid is the first step toward the future mosaic without
  committing yet to a full free-layout container

Near-term hierarchy rule:

- `Core` should not read like just another add-on card
- when the launcher grows into a small grid, separate `Core` from the add-on
  block explicitly
- this is still a launcher hierarchy, not yet the final mosaic itself

Important rule:

- this launcher is still only for choosing a workspace
- it is not yet the final panel mosaic
- do not mix this step with docking, free arrangement, or arbitrary multi-panel
  layouts

## Workspace Overview

The body-level step toward a future mosaic should stay modest: a small workspace
overview block, using cards like the launcher's, that lets the user see the
available domains without a full layout editor. When a workspace has an active
panel the overview should reflect it rather than staying generic, surfacing the
panel's runtime id as a secondary line and giving quick access to that
workspace's local panel stack, so overview and active host cooperate instead of
reading as separate surfaces. Once several workspaces exist it may separate the
current one and group the rest as `Core` and `Add-ons`.

**It is a navigator, not a multi-panel container.** It should reinforce the
workspace model already in the shared header, and the final mosaic — if it ever
comes — should grow out of that shared language rather than replace it abruptly.

**Scaling direction.** `Core` is the native workspace; larger add-ons may
contribute their own, each with its own internal panel stack; smaller add-ons
stay lighter, as context actions, panel sections, export helpers and shapes. So
the future pressure is not "more panels in one flat pile" but "more workspaces,
each with a calmer local stack".

### What the runtime does today

The shared panel shell has a workspace switcher that appears only when more than
one workspace is effective — a workspace contributing no visible panel or section
runtime does not pollute the launcher. The header stays calm: only the current
workspace is visible as the trigger, with a compact subtitle for the active
domain, and the full set appears when it is opened. Entries may summarise what
they contain (panel count, section count, lightweight runtime hints) and mark the
current workspace, so it reads as a domain selector rather than a raw dropdown.

Outside `Core`, the Studio panel disappears as an operative panel, and returning
to `Core` restores the last core panel instead of forcing it. Non-core workspaces
stay workbench-centric and can offer a direct return to `Core`; the runtime must
not imply that every add-on workspace already has a full native panel stack.

The Add-ons panel materialises a generic panel-stack bridge for add-on
workspaces: a panel selector for the current workspace and a generic active-panel
host that also absorbs workspace-specific sections and the active add-on's
immediate capabilities (context actions, export helpers), so a panel and its
add-on runtime do not feel artificially split. It is still not arbitrary add-on
frontend UI. That selector has moved up into the shared header, which now reads
in two levels: workspace launcher first, panel stack inside the active workspace
second.

Optional MolSysSuite add-ons should normally surface themselves through this
path.

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

Both built-in panels should share the same base
container.

Reason:

- visual stability
- one clear mental model of panel mode
- switching panel should feel like changing workspace content, not opening a
  different window system

### Preferred Size Direction

Roughly `68-74%` of the canvas in width and `62-72%` in height, centred on
about `72%` by `68%`.

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

## Where this stands today

**Checked against the running widget on 2026-08-06.** The design *targets* above
still stand: the quiet canvas, the two interaction doors, three permanent shell
controls, the row grammar, the state hierarchy. The panel *taxonomy* does not.

| what this file proposed | what exists |
|---|---|
| `Navigate` + `Workbench`, two panels | **Studio + Add-ons**, with ten Studio subpanels: System, Whole, Selections, Regions, Annotations, Measures, Shapes, Layers, Viewport, Export |
| `tabs` first, discreet carousel later | tabs shipped (`TabKey`, `group-panel.ts`); the carousel was never built |
| `controls_mode="classic"` default, `"minimal"` opt-in | **`"minimal"` is the default** |
| `panel_mode_style="drawer"` default, `"floating"` opt-in | **`"integrated"`**, with `classic` / `integrated` / `cinema` offered in the context menu |
| `viewer_mode` | did not exist when this was written; `"integrated"` today |

The two-panel taxonomy, its internal sections and layouts, and the navigator
alternatives are in
[`archive/canvas_panel_taxonomy_2026_04.md`](archive/canvas_panel_taxonomy_2026_04.md),
together with the transition plan that carried the defaults across
(`archive/canvas_panel_transition.md`).

**The open questions this file used to carry were about that taxonomy**, so they
are archived with it rather than restated here. Anything still genuinely open
should be re-derived against the shipped Studio; a question about a panel that
was never built is not an open question.

What remains decided at the canvas level, and is not up for rediscovery:

- the resting canvas stays visually quiet, molecule first;
- the trajectory scrubber is the only always-visible data control, and only when
  there is a trajectory;
- the two doors for non-programmatic use are the right-click context menu and
  panel mode;
- only three permanent shell controls live on the canvas — panel, fullscreen,
  popup — and scene-facing actions (`background`, `spin`, `swing`, camera reset)
  stay out of that cluster;
- the same panel model works in the notebook canvas and in the popup.

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
