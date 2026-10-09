(canvas-context-menu)=
# Using the canvas context menu

Right-click a molecular group, a shape, an annotation, a measurement or an
interaction to act on that object. Right-click empty space for scene controls.
Right-drag still pans the scene.

Opening the menu preserves your active selection. The object you right-clicked
is the **target**; your working selection appears in a separate **Active
selection** submenu. Creating something from the target does not replace your
selection.

## Working with a molecular target

| Menu | What you can do |
| --- | --- |
| Focus Target | Frame the target in the canvas. |
| Inspect Target | Open its details in Studio → System. |
| Select | Replace, add to or remove from the selection using Pointed atom, Group or Chain. |
| Create | Create a region or annotation; open Shapes in Studio with the target as its anchor. |
| Measure | Start a distance, angle or dihedral measurement with an explicit endpoint policy. |
| Interactions | Inspect existing analyses or prepare a calculation in Studio. |

**Group** means a molecular group: an amino acid, nucleotide, water, ion or
small molecule. It differs from a **Region**, which you define yourself.

Region and annotation forms let you choose **Target atoms**, **Pointed atom**,
**Group** or **Chain**. Pointed atom requires an unambiguous atom pick. If the
loaded system declares no group or chain membership for the target, that scope
is unavailable and explains why. Rendering labels do not establish membership.

The measurement menu distinguishes centers of picked atom sets, individual
atoms and an explicitly chosen representative atom. Distances use Å; angles
and dihedrals use degrees. The canvas indicates the remaining picks.

Opening **Calculate for Target** does not perform a calculation. Studio asks
you to choose a name, method and structures, then submit. Interactions remains
experimental; see {doc}`../overlays/interactions` for its scientific limits.

## Working with selections and objects

**Active selection** offers focus, inspection, saving, region/section creation,
annotations, expansion and clearing. Spatial expansion presets use 3, 5 or 8 Å.
Actions that require atoms are unavailable for selections containing only
unanchored scene objects.

Object menus offer focus, selection of associated atoms where available,
editing in Studio, hiding and deletion. A free-position shape can be focused
using its geometry even when it has no associated atoms. Destructive actions
are separated visually from the other actions.

An interaction menu distinguishes **this interaction** from its **interaction
set**. Inspect, select or focus the participants of the picked occurrence in
the current structure. Hiding or deleting its representation keeps the stored
analysis. Changing structure or replacing/filtering the analysis invalidates
the old occurrence context.

**Related regions** offers up to eight matching regions with focus, visibility
and access to their Studio editor. Saved selections open their collection in
Studio. See {doc}`../scene_management/visibility` for region visibility rules.

## Navigating the menu

Click a category to open its secondary menu beside the main menu. Click the
same category again to close it, or another category to switch. Hovering never
opens a category. Near a canvas edge, the secondary menu opens to the left;
on a narrow canvas, it replaces the main menu and provides **Back**.

Use arrow keys, Home/End and Enter/Space. Escape returns one level or closes
the menu before cancelling a measurement tool or clearing a selection.
Unavailable actions can receive keyboard focus to explain their limitation,
but cannot run. Inputs and dropdowns keep their normal keyboard behavior.

## View modes and discovering controls

**View** offers Reset View, background, rotation, swing and Classic, Integrated
or Cinema mode. Undo/Redo follows the available scene history. **Open Studio**
opens the section appropriate to your target; **Help** opens canvas help.

By default, canvas buttons appear near their area and hide when you leave it.
When first available on a new canvas or after changing mode, they appear for
two seconds to show you where they are. They fade together; Cinema's trajectory
scrubber also slides down. Cinema has no viewport button bar.

In Settings, choose **Buttons** or **Entire canvas** as the reveal area.
The Python equivalent is `view.set_controls_visible(True, autohide=True,
autohide_scope="controls")`; use `autohide_scope="canvas"` for the entire canvas,
or `autohide=False` to keep enabled controls visible. Explicit hiding takes
precedence. Dock and fullscreen keep the same reveal policy.

Exported pages offer the actions their host can support. Molecular changes
requiring a live Python backend are not advertised in a static export.
