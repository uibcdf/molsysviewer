# Introduction

MolSysViewer pairs a Mol* renderer with a lightweight AnyWidget bridge so you can control a 3D scene from Python.

Key concepts
- Load structures from strings, URLs, or MolSysMT payloads (`load_*` helpers).
- Python sends JSON-like messages to the frontend to add shapes and overlays.
- Tags let you group shapes and clear them selectively.
- You can combine MolSysMT selections with MolSysViewer styles for rich overlays.

What you’ll find in this guide
- A quick mental model of the Python ↔ JS bridge.
- How to load data and show the widget the first time.
- Where to look for shape-specific options (pockets, channels, pharmacophore, ellipsoids).

```{toctree}
:hidden:
:maxdepth: 1
```
