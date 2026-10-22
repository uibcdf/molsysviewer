(User_Intro_What)=
# What is MolSysViewer?

MolSysViewer is a Python library for interactive 3D molecular visualization in Jupyter.
It gives you a friendly, Python-first way to drive a Mol\* scene: you load data, choose
representations, add scientific overlays, and export shareable views.

If you have ever felt that a notebook cell should be able to say “show me this protein,
highlight this pocket, add a pharmacophore, and keep it reproducible”, MolSysViewer is
built for that workflow.

## How it fits in MolSysSuite

MolSysViewer is one of the foundational tools in [**MolSysSuite**](https://www.uibcdf.org/molsyssuite), together with
[MolSysMT](https://www.uibcdf.org/molsysmt). Other projects in the suite (for example [ElastNetMT](https://www.uibcdf.org/elastnetmt), [TopoMT](https://www.uibcdf.org/topomt), and
[PharmacophoreMT](https://www.uibcdf.org/pharmacophoremt)) build on top of them to support real scientific workflows in
computational biology, molecular modeling, and molecular design.

## Powered by Mol\*

At the same time, MolSysViewer stands on the shoulders of a third-party project:
[**Mol\***](https://molstar.org/). Mol\* is the rendering engine that draws the scene in the browser.
We are not the authors of Mol\*. We rely on it because it is a powerful, modern
molecular viewer, and we are genuinely grateful to the Mol\* developers for making
it available to the community.

In a nutshell:

- **MolSysMT** helps you describe molecular systems (structures, trajectories, selections).
- **MolSysViewer** gives you a Python API to visualize those systems interactively.
- **Mol\*** does the rendering and interactive graphics in the browser.

You do not need to learn Mol\* internals to be productive. Most of the time you will
work with a single object: {class}`molsysviewer.viewer.MolSysView`.

## A gentle mental model

It helps to think of MolSysViewer as having two halves:

- **Python side (your notebook):** you call methods like `view.load(...)`,
  `view.whole.set_representation(...)`, or `view.shapes.add_pocket_surface(...)`.
- **Browser side (the viewer):** Mol\* renders the scene and reacts to your commands.

In practice, this means you get the interactivity of a web viewer, but you keep the
control and reproducibility of a notebook.

## What you can do with it

Here are the main things you will do in day-to-day use:

- **Load structures and trajectories** with `view.load(...)` and work with selections.
- **Choose how things look** by applying representations to the whole system or to
  specific regions.
- **Manage visibility and scene state** (show/hide/isolate, camera, reset and cleanup).
- **Add overlays (shapes)** such as pockets, channels, pharmacophore features, links,
  anisotropy glyphs, and meshes, and organize them with tags and layers.
- **Export reproducible views** as lightweight HTML with `view.export.html(..., shared_runtime=...)`,
  which is especially useful for documentation, reports, and sharing results.

## Where visualization ends and add-ons begin

You can use MolSysViewer without add-ons to visualize and explore molecular
systems, manage scene objects and share reproducible views. MolSysMT supplies
the scientific backend; you do not register an add-on to load a system or use
the native scene tools.

Visualization can include a calculation. For example, the experimental Interactions
tools can calculate supported hydrogen bonds and display them. A request such
as coloring groups by solvent-accessible surface area (SASA) also fits this
visual purpose, but that convenience workflow is not currently implemented.
Each tool's documentation describes its actual availability and scientific
options.

Add-ons provide additional analysis, molecular preparation and editing tools,
and specialized domain models. Hiding waters changes the scene; removing their
atoms edits the system. Displaying principal axes adds a visual aid; aligning
molecular coordinates to them edits the system. Those edits belong to the
scientific tools and their integration with the view.

A visual request must not silently protonate, repair or align your system.
You choose the relevant scientific parameters and any preparation explicitly.
Scientific results and their representations are separate: hiding an
interaction set does not delete its analysis or require another calculation
when you show it again.

See {doc}`addons` for extension availability and {doc}`molsysmt` for the backend
and Python integration. A redesigned MolSysMT tools add-on is planned; the
retired legacy add-on is not supported by the current runtime.

## Try it (first contact)

If you do not have MolSysViewer installed yet, start with {doc}`installation`.
Then come back here and try this first “hello world”.

```python
import molsysviewer as msv

view = msv.MolSysView()
view.show()
```

In the next pages, you will learn how to load real molecular systems and how to make the
viewer reflect the questions you are asking.
