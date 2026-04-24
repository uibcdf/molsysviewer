# Canvas Panel Transition Strategy

This document records the coexistence and transition strategy for the canvas
panel architecture and controls surface.

It is a companion to `canvas_minimal_ux.md`, which remains the authoritative
design target.

The purpose of this document is different:

- `canvas_minimal_ux.md` describes **where we want to arrive**
- this document describes **how we navigate from the current implementation
  to that target** without breaking what already works

This document is intentionally temporary.
When the transition is closed — that is, when a single default is established
and the alternative is deprecated — this document should be archived or removed.

## Current State vs. Design Target

The design target is documented in full in `canvas_minimal_ux.md`.
The current implementation diverges in two independent dimensions.

### Dimension 1: Canvas Controls Surface

**Target:**
- Three permanent meta-controls: `panel`, `fullscreen`, `popup`
- Small SVG icons with minimal stroke language, grouped in one cluster
- Scene-facing actions (`background`, `spin`, `swing`, `reset`) removed from the
  permanent surface and absorbed into the context menu or the Workbench Scene section

**Current state (as of 2026-04-20):**
- Six text-label buttons: `Reset`, `Full`, `Bg`, `Spin`, `Swing`, `Pop`
- No SVG icons — plain text labels with basic button styling
- Scene-facing actions still present as permanent controls
- The `panel` toggle exists but is not part of this control cluster
- Implemented in `molsysviewer/js/src/ui/controls.ts`

### Dimension 2: Panel Mode Container Architecture

**Target:**
- One floating panel, centered vertically and horizontally over the canvas
- ~72% canvas width, ~68% canvas height
- Rounded corners, neutral translucent background
- Disappears fully when closed
- Tabs as navigator (Navigate / Workbench)

**Current state (as of 2026-04-20):**
- Drawer architecture: Navigate anchored left (560px fixed width), Workbench
  anchored right (360px fixed width)
- Full canvas height; translate-based slide animation
- 26px toggle strip remains visible when closed
- Pill-button navigation (not tabs) between Navigate and Workbench
- Implemented in `molsysviewer/js/src/ui/panel-shell.ts`,
  `group-panel.ts`, `workbench-panel.ts`

## Coexistence Decision

**Decision (2026-04-20):** Do not eliminate the current design.
Implement the target design as a parallel mode.
Let the user choose between them while both are available.

**Rationale:**

The current drawer design has real qualities that the floating design is not yet
proven to match in a scientific visualization context:

- stable spatial memory (left = Navigate, right = Workbench)
- always accessible without capturing the canvas
- familiar to users of panel-heavy scientific tools

The floating panel is the UX direction prescribed by the design spec, and it is
likely better for the minimal-canvas goal, but that claim should be validated
with actual use rather than assumed.

Replacing the drawer before the floating design is proven would risk:

- regression in usability for existing users
- loss of a tested, working surface while the replacement is still unverified

Keeping both as selectable modes avoids that risk and allows direct comparison.

## Configuration Seam

The coexistence is expressed through two independent configuration axes.

### Axis 1: `controls_mode`

Controls which set of canvas surface buttons is rendered.

| Value | Behavior |
|-------|----------|
| `"classic"` | Current six-button set (Reset, Full, Bg, Spin, Swing, Pop) with text labels |
| `"minimal"` | Three-control cluster (panel, fullscreen, popup) with SVG icons |

Default: `"classic"` until `"minimal"` is validated.

Implementation seam: `buildControls()` in `controls.ts`.
The `classic` path is the current code.
The `minimal` path adds a parallel branch that renders the three-icon cluster
and omits the scene-facing buttons.

Scene-facing actions (`background`, `spin`, `swing`, `reset`) must be available
through the context menu or the Workbench Scene section before `"minimal"` can
be the default.
Do not switch the default until those alternatives exist and are tested.

### Axis 2: `panel_mode_style`

Controls the container architecture for panel mode.

| Value | Behavior |
|-------|----------|
| `"drawer"` | Current drawer architecture (left/right anchored, full height, translate slide) |
| `"floating"` | Target floating panel (centered, percentage-based size, tabs) |

Default: `"drawer"` until `"floating"` is validated.

Implementation seam: the panel content (`group-panel.ts`, `workbench-panel.ts`)
is already independent from the shell (`panel-shell.ts`).
The floating container is a second shell implementation that hosts the same
content panels.
Do not duplicate panel content logic — only duplicate the container/chrome.

### Where the parameters live

Both axes should be exposed at the Python viewer construction level:

```python
view = MolSysView(
    controls_mode="classic",       # or "minimal"
    panel_mode_style="drawer",     # or "floating"
)
```

These should also be passable through the existing viewer config path so that
the JS side receives them at initialization rather than as runtime messages.

## Prerequisite: Scene Actions Before `controls_mode="minimal"` Is Default

Before `controls_mode="minimal"` can become the default, the following must
exist:

- `background` toggle available from the empty-canvas context menu
- `spin` toggle available from the empty-canvas context menu
- `swing` toggle available from the empty-canvas context menu
- `reset camera` available from the empty-canvas context menu or a
  Workbench Scene section

Until these alternatives exist, switching to `"minimal"` would silently remove
user-facing controls with no replacement path, which is a regression.

## Transition Horizon

These modes should not remain open indefinitely.

Proposed horizon: during `0.16.x`, both modes are available and the default
remains `"classic"` / `"drawer"`. The floating and minimal modes are
experimentally available for testing.

At the `0.16.x` → `0.17.x` boundary:

- if `"floating"` + `"minimal"` are proven better: flip the defaults, mark
  the classic/drawer modes as deprecated, plan removal in `0.18.x`
- if the drawer proves better or the decision is not clear: document that
  explicitly and keep the drawer as the permanent default; close or archive
  this document

**The decision must be closed.** Indefinite coexistence is not a valid
long-term state — it doubles the maintenance surface without clear benefit.

## Closing Criteria

A mode can be promoted to default when:

1. It has been usable for at least one release cycle without regression reports
2. The prerequisite scene actions are available through alternative surfaces
3. At least one non-trivial scientific workflow has been tested through it
4. The implementation does not require maintaining substantially divergent code
   paths for panel content

A mode can be deprecated when:

1. Its replacement has been the default for at least one release cycle
2. No known user workflow depends on it uniquely
3. Its removal is announced in `changes_notes.md` with the relevant release

## What This Document Is Not

This document does not override the design decisions in `canvas_minimal_ux.md`.
The target described there is still the target.

This document only records the strategy for reaching that target while
preserving the current working implementation during the transition period.

When this transition is closed, update or archive this document.
Do not let it become a permanent justification for keeping both modes alive.
