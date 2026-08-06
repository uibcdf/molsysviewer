# MolSysViewer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18072956.svg)](https://doi.org/10.5281/zenodo.18072956)
[![](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![Documentation](https://github.com/uibcdf/molsysviewer/actions/workflows/sphinx_docs_to_gh_pages.yaml/badge.svg)](https://github.com/uibcdf/molsysviewer/actions/workflows/sphinx_docs_to_gh_pages.yaml)
[![CI](https://github.com/uibcdf/molsysviewer/actions/workflows/CI.yaml/badge.svg)](https://github.com/uibcdf/molsysviewer/actions/workflows/CI.yaml)
[![codecov](https://codecov.io/github/uibcdf/molsysviewer/graph/badge.svg?token=9ZMA4YZLOR)](https://codecov.io/github/uibcdf/molsysviewer)
[![Install with conda](https://img.shields.io/badge/Install%20with-conda-brightgreen.svg)](https://conda.anaconda.org/uibcdf/molsysviewer)

*A Mol\*-powered interactive molecular viewer for Jupyter, built around the idea that
exploratory science should become reproducible science.*

MolSysViewer is a modern 3D molecular visualisation tool built on the
[Mol\*](https://molstar.org) engine and exposed through a clean Python API.
It renders structures, trajectories, and scientific overlays directly inside
Jupyter notebooks and JupyterLab — and it is designed so that every meaningful
thing you do interactively can be captured as replayable, exportable Python state.

Documentation: https://www.uibcdf.org/molsysviewer

---

## Features

### Interactive 3D visualisation
- Load PDB/mmCIF strings, remote PDB IDs, URLs, or native MolSysMT systems
- High-quality Mol\* rendering: cartoon, surface, ball-and-stick, spacefill, and more
- Built-in representation styles and publication-ready presets
- Multi-structure trajectory playback with configurable frame rate

### Python-driven scene management
- **Regions** — named atom subsets with independent visibility, colour, and representation
- **Layers** — non-structural visual groups (shapes, overlays) with tag-based lifecycle
- **Styles** — reusable scene recipes applied globally or per region
- `view.whole`, `view.regions`, `view.layers` as first-class Python objects

### Scientific overlays (shapes)
- Displacement vectors, link shapes, H-bond overlays, anisotropy ellipsoids
- Pocket blobs, pocket surfaces, channel tubes
- Pharmacophore glyphs (donors, acceptors, hydrophobic patches, aromatic rings)
- Sphere and triangle-face primitives
- All shapes are structure-aware: they follow atoms across trajectory frames

### Annotations and measurements
- Persistent labels anchored to atom selections (`view.annotations`)
- Interactive distance, angle, and dihedral measurements (`view.measurements`)
- Canvas pickability: hover and click events on labels and measurements
- All artifacts survive export/replay/rebuild cycles

### Canvas interaction and callbacks
- Click, hover, and context-menu events forwarded to Python
- `region_tags` enrichment on every interaction payload
- `view.on_hover(fn)` / `view.on_click(fn)` reactive callbacks
- Active selection bridge: canvas selection → named region/selection/label

### Export and embedding
- `view.export.html(...)` — self-contained interactive HTML (standalone or CDN-lite)
- `view.export.figure(...)` — publication-quality PNG/SVG snapshots
- `view.export.figure_publication_set(...)` — full light/dark/transparent bundle
- `view.movie.export(...)` — animated GIF or MP4 from trajectory frames
- State serialisation: `view.export_state()` / `view.import_state()`

### Addon system
MolSysViewer has a first-class addon API that lets external packages add
workspaces, panels, context actions, and shape providers without modifying the core:

| Addon package | Ecosystem tool | What it adds |
|---|---|---|
| `molsysviewer-molsysmt` | MolSysMT | 10-panel workspace: inspect, select, colour, H-bonds, topology, PBC, mechanics, build |
| `molsysviewer-elastnetmt` | ElastNetMT | GNM/ANM elastic network modes and contact network overlays |
| `molsysviewer-topomt` | TopoMT | Pocket detection and topography visualisation |
| `molsysviewer-pharmacophoremt` | PharmacophoresMT | Structure-based pharmacophore glyph overlays |

### Canvas UX modes
- `controls_mode="minimal"` — 3-icon cluster + keyboard shortcuts (N/W/H)
- `panel_mode_style="floating"` — centred overlay panel, no viewport shift

---

## Quick start

```python
import molsysviewer as msv

# A PDB ID, a local file, or a URL
view = msv.new_view("1TRS")
view.show()
```

### There is nothing to convert

Objects you already have in memory go straight in:

```python
import mdtraj as md
import molsysmt as msm
import molsysviewer as msv

traj = md.load(msm.systems["pentalanine"]["traj_pentalanine.h5"])
view = msv.new_view(traj)           # an mdtraj.Trajectory: 62 atoms, 5000 structures
```

MDAnalysis `Universe` and `AtomGroup` objects, OpenMM topologies, and a long
list of file formats work the same way: `new_view` hands whatever you give it to
[MolSysMT](https://github.com/uibcdf/MolSysMT)'s `convert`, so anything MolSysMT
reads is accepted. Selections can be written in MolSysMT's own syntax or in
MDTraj's (`syntax="MDTraj"`).

### Regions: named subsets that keep their own appearance

```python
view = msv.demo["1TCD"]                  # triosephosphate isomerase, a dimer
view.make_regions_by(element="chain")    # -> "A", "B", and the waters "A__2", "B__2"

view.regions["A"].set_representation("cartoon")
view.regions["A"].set_color("teal")
view.regions["B"].set_representation("spacefill")
view.regions["B"].hide()                 # a region can hide once it draws itself
```

### Scientific overlays

```python
import numpy as np
import pyunitwizard as puw

atom_indices = view.regions["A"].atom_indices
view.shapes.add_displacement_vectors(    # e.g. an ANM mode
    origins=None,                        # None -> use the current atom positions
    vectors=puw.quantity(np.random.randn(len(atom_indices), 3) * 0.5, "angstroms"),
    atom_indices=atom_indices,
    tag="anm-mode-0",
)
```

Magnitudes carry units throughout the suite: a bare array is refused rather than
silently assumed to be in Å.

### Export, and addons

```python
view.export.html("my_scene.html", title="TIM — chain A")
```

```python
msv.addons.register_module("molsysviewer_molsysmt")   # a 10-panel MolSysMT workspace
```

### The point: exploration becomes state

Everything above — and everything you do by hand in the Studio panel — is scene
state, and scene state is a plain dictionary:

```python
import json

state = view.export_state()
json.dump(state, open("scene.json", "w"))

# later, on another machine, or as a paper's supplementary material
restored = msv.demo["1TCD"]
restored.import_state(json.load(open("scene.json")))
```

`restored` now carries the same regions, colours, representations, visibility and
overlays as the view you had been clicking around in. That round trip — not the
feature list above — is what MolSysViewer is for.

---

## Installation

Conda (recommended):

```bash
conda install molsysviewer -c uibcdf
```

Pip:

```bash
pip install molsysviewer
```

---

## Development

MolSysViewer uses Python for the API and widget layer, TypeScript + Mol\* for
rendering, and esbuild for bundling.  The JS bundle (`viewer.js`) is tracked in
the repository and ships inside the wheel/conda package so that users never need
a Node.js toolchain.

```bash
# Install in editable mode
pip install -e .

# Rebuild the JS bundle (only needed when editing TypeScript sources)
cd molsysviewer/js
npm install
npm run build

# Run the test suites
pytest tests/                              # Python
npm --prefix molsysviewer/js run test:js   # JS unit tests
```

Developer guide: https://www.uibcdf.org/molsysviewer/content/developer/

---

## Ecosystem

MolSysViewer is the visualisation engine for the **UIBCDF MolSys ecosystem**:

- **MolSysMT** — molecular systems and trajectories
- **TopoMT** — cavity and topography analysis
- **PharmacophoresMT** — pharmacophore modelling
- **ElastNetMT** — elastic network models

---

## License

MIT License.

MolSysViewer uses the [Mol\*](https://molstar.org) engine developed by the Mol\* team and RCSB PDB.
