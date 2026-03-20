# Add-ons

MolSysViewer can grow with optional **add-ons**.

The core viewer should stay focused on:

- molecular systems and trajectories
- navigation and workbench state
- shapes, annotations, measurements, and styles
- reproducible scene/export behavior

Optional scientific domains can then extend that core without inflating it for
everyone.

Examples include future add-ons for:

- topography and cavities
- pharmacophores
- elastic networks
- allostery-related overlays

## Installation model

The expected installation pattern is:

- a scientific/domain package
- plus an optional MolSysViewer integration package

For example:

- `topomt`
- `molsysviewer-topomt`

This keeps the scientific library usable on its own while making the viewer
integration optional.

## Discovery model

MolSysViewer now has a first explicit add-on registry at the host level:

```python
import molsysviewer

molsysviewer.addons.discover()
```

Discovery currently checks a small maintained list of recognized add-on
modules. Missing add-ons are ignored without error.

If an add-on is available in the environment, a view can use it without
re-registering it manually for every viewer instance.

## What a user should expect

When add-ons become available, they should normally appear as:

- optional new panels
- optional workbench contributions
- optional context actions

The resting viewer should remain clean.
Add-ons should mostly extend the structured workspace, not add permanent visual
noise to the canvas.

## Current status

The add-on platform now exists in the API and internal tests.

Real user-facing MolSysSuite add-ons are still a next step, but `1.0` is being
shaped so that those add-ons can attach cleanly when they arrive.
