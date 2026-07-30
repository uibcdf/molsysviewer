# Canvas Panel Transition Strategy

**Status:** completed historical transition plan. Current panel behavior is
defined by the runtime and public viewer configuration.

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
| `"focus"` | 100% clean canvas with no permanent controls; relies on keyboard shortcuts and context menu |

Default: `"classic"` until `"minimal"` or `"focus"` is validated.

Implementation seam: `buildControls()` in `controls.ts`.
The `classic` path is the original code.
The `minimal` path renders the three-icon cluster and omits the scene-facing buttons.
The `focus` path hides all controls and renders a temporary helper toast upon initialization.

### Axis 2: `panel_mode_style`

Controls the container architecture for panel mode.

| Value | Behavior |
|-------|----------|
| `"drawer"` | Original drawer architecture (left/right anchored, full height, translate slide) |
| `"floating"` | Target floating panel (centered, percentage-based size, separate shells for Navigate/Workbench) |
| `"floating-unified"` | Unified floating panel (single shared shell, tab-based navigation, drag, opacity, minimize) |
| `"ambient"` | Glassmorphism floating panel (high blur, translucent dark base, transparent click-through backdrop) |
| `"split"` | Docked overlay vertical panel (narrow strip on the left, transparent click-through backdrop on the right) |

Default: `"drawer"` until a floating/unified mode is validated.

Implementation seam: the panel content (`group-panel.ts`, `workbench-panel.ts`) is independent from the container shell.
The floating container shells (`FloatingPanelShell`) host the same content panels.
In `"floating-unified"`, `"ambient"`, and `"split"`, both panels share a single coordinated shell, avoiding visual overlaps.

### Where the parameters live

Both axes, along with the high-level preset parameter `viewer_mode`, are exposed at the Python viewer construction level:

```python
view = MolSysView(
    viewer_mode="classic",         # "classic", "classic-floating", "zen", "integrated", "ambient", "focus", "split"
    controls_mode=None,            # Explicit override
    panel_mode_style=None,         # Explicit override
)
```

The high-level `viewer_mode` preset maps to the following combinations:
- `"classic"` (default): `controls_mode="classic"`, `panel_mode_style="drawer"`
- `"classic-floating"`: `controls_mode="classic"`, `panel_mode_style="floating"`
- `"zen"`: `controls_mode="minimal"`, `panel_mode_style="floating"`
- `"integrated"`: `controls_mode="minimal"`, `panel_mode_style="floating-unified"`
- `"ambient"`: `controls_mode="minimal"`, `panel_mode_style="ambient"`
- `"focus"`: `controls_mode="focus"`, `panel_mode_style="floating-unified"`
- `"split"`: `controls_mode="minimal"`, `panel_mode_style="split"`

## Prerequisite: Scene Actions Before `controls_mode="minimal"` Is Default

Before `controls_mode="minimal"` can become the default, the alternative surfaces for scene actions must exist.
*Status (2026-06-25):* The prerequisites are fully met. The empty-canvas context menu now provides:
- `Reset View` (Reset camera)
- `Toggle Background`
- `Toggle Spin`
- `Toggle Swing`

These options are functional and validated.

## Transition Horizon & Decision Plan

These modes should not remain open indefinitely. The experimental phase with the expanded suite of modes (`classic`, `classic-floating`, `zen`, `integrated`, `ambient`, `focus`, `split`) is designed for exploration and evaluation during version `0.14.x`.

At the `0.14.x` → `0.15.x` boundary:
- **Decision to close:** We must decide on a single new default and deprecate redundant modes. Keeping 7 modes indefinitely doubles the maintenance and documentation surface.
- **Proposed Target:** Promote `integrated` (or `split`) as the new default layout, keeping `classic` as an optional legacy fallback, and deprecate `classic-floating` and `zen`.

## Evaluation and Validation Plan (Experimental Phase)

During the `0.14.x` cycle, the following criteria and questions must be studied and resolved to close the transition:

### A. Scientific Workflow Validation
Test the new modes in real-world, non-trivial notebooks (e.g., trajectory analysis, pockets, or pharmacophores) to evaluate:
- **Ergonomics (Split vs. Integrated):** Does `split` (Side-HUD) mode provide a significantly more comfortable and fast workflow for residue selection than opening/closing the central card in `integrated`?
- **Visual Fatigue in Ambient Mode:** Does the translucent *glassmorphism* card in `ambient` mode remain comfortable for reading long residue lists over complex molecular structures, or does it cause eye strain?
- **Cinema Accessibility:** Does the self-dismissing helper toast in `focus` mode successfully guide first-time users without cluttering the canvas, or do they still struggle with keyboard shortcuts?

### B. Keyboard Shortcut Conflicts
Since `focus` and floating modes rely heavily on shortcuts (`N`, `W`, `H`, `Esc`):
- **Audit focus capture:** Test if pressing `Esc` or `H` conflicts with global shortcuts in JupyterLab, classic Jupyter notebooks, or VS Code.
- Ensure that shortcuts are only captured when the visualizer canvas has focus or that they do not block standard notebook cell operations.

### C. Responsiveness & Split-Screen Performance
- Test the elastic resizing (`resize: both`) of the floating panels when the Jupyter workspace is split side-by-side.
- Evaluate if the fixed `330px` width of the `split` panel is too wide in narrow side-by-side celdas, and determine if `split` mode should also support elastic resizing.

### D. Export and Serialization Parity
- Verify that state-based properties (e.g., whether the panel is minimized, the current opacity index, and the active panel tab) are correctly serialized and restored.
- Confirm that standalone static HTML exports (`view.export.html()`) render the new modes (`ambient`, `split`, `focus`) perfectly without a running Python backend.

## Closing Criteria

A mode can be promoted to default when:

1. It has been usable for at least one release cycle without regression reports.
2. The prerequisite scene actions are fully validated through alternative surfaces (context menu).
3. At least one non-trivial scientific workflow has been verified.
4. The implementation maintains a unified, non-divergent code path (achieved via the shared shell in `FloatingPanelShell`).

A mode can be deprecated when:

1. Its replacement has been the default for at least one release cycle.
2. No known user workflow depends on it uniquely.
3. Its removal is announced in `changes_notes.md`.

## What This Document Is Not

This document does not override the design decisions in `canvas_minimal_ux.md`.
The target described there is still the target.

This document only records the strategy for reaching that target while
preserving the current working implementation during the transition period.

When this transition is closed, update or archive this document.
Do not let it become a permanent justification for keeping both modes alive.
