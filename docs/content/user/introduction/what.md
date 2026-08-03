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

## What MolSysViewer is not

MolSysViewer is not a molecular simulation engine, a force-field toolkit, or a structure
preparation pipeline. It is focused on visualization and on making visual results easy
to reproduce and communicate.

## Try it (first contact)

If you do not have MolSysViewer installed yet, start with {doc}`installation`.
Then come back here and try this first “hello world”.

```python
import molsysviewer as viewer

view = viewer.MolSysView()
view.show()
```

In the next pages, you will learn how to load real molecular systems and how to make the
viewer reflect the questions you are asking.
