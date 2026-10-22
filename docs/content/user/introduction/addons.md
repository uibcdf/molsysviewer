# Add-ons

MolSysViewer can grow with optional **add-ons**.

The core viewer provides visualization and exploration without add-ons:

- molecular systems and trajectories
- navigation and workbench state
- shapes, annotations, measurements, and styles
- reproducible scene/export behavior

It can also calculate supported scientific results directly for visual use,
such as hydrogen bonds in experimental Interactions. Selection, structure scope and method
remain explicit. Scientific results can outlive their representations; hiding
an overlay does not remove its data.

Add-ons extend this with additional analysis, molecular preparation and editing
tools, and specialized scientific models. The distinction follows your intent:
coloring a system by a calculated property is visual; changing its chemical
composition or fitting its coordinates is a molecular operation. Being able to
draw a result does not move an entire specialized workflow into the core.
See {doc}`what` for the product boundary.

Domain extensions include tools for:

- topography and cavities
- pharmacophores
- elastic networks
- allostery-related overlays

## Installation model

MolSysSuite toolkits normally ship their Viewer integration inside their own
package, for example the `molsysviewer_pharmacophoremt` module supplied by
PharmacophoreMT. Follow that toolkit's installation instructions. External
add-ons can also use a separate distribution. The scientific library remains
usable independently of its Viewer panels.

MolSysMT itself remains a required backend even when you use no add-ons.
An optional tools interface and the backend dependency have different roles.

## Discovery model

MolSysViewer now has a first explicit add-on registry at the host level:

```python
import molsysviewer

molsysviewer.addons.discover()
```

Discovery uses declared package entry points and a maintained list of recognized
integration modules. Manual registration is also available. Missing optional
add-ons are ignored without error.

If an add-on is available in the environment, a view can use it without
re-registering it manually for every viewer instance.

Project-level defaults can also be applied explicitly from `_molsysviewer.py`:

```python
import molsysviewer

molsysviewer.addons.load_project_config("_molsysviewer.py")
```

That lets a project declare which add-ons should be enabled or disabled by
default before new views are created.

## What a user should expect

Available add-ons normally contribute:

- optional new panels
- optional workbench contributions
- optional context actions

The resting viewer should remain clean.
Add-ons should mostly extend the structured workspace, not add permanent visual
noise to the canvas.

## Current status

The add-on platform is implemented. Each toolkit documents the availability and
limits of its integration; a generic shape renderer does not imply a complete
scientific workflow. The {doc}`../../showcase/addons` catalogue records current
provider status.

A redesigned MolSysMT tools add-on is planned for additional molecular tools.
Its supported functions, update behavior and installation are still being
designed. The old `molsysviewer_molsysmt` integration is retired and rejected by
the current runtime; there is no supported `view.addons.molsysmt` interface yet.
Current loading, selections, Interactions and explicit Python integration
remain available through their documented APIs.
