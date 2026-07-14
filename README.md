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

# Load a structure directly from the Protein Data Bank
view = msv.new_view("1TRS")
view.show()
```

```python
# Create named regions and control visibility independently
backbone = msv.new_view("1TRS")
backbone.make_regions_by(element="chain")
backbone.regions["chain-A"].hide()
backbone.regions["chain-B"].show()
```

```python
# Add a displacement-vector overlay (e.g. ANM mode)
import numpy as np
view.shapes.add_displacement_vectors(
    vectors=np.random.randn(n_atoms, 3) * 0.5,
    atom_indices=list(range(n_atoms)),
    tag="anm-mode-0",
)
```

```python
# Export an interactive HTML snapshot
view.export.html("my_scene.html", title="TIM — chain A")
```

```python
# Use the addon system
import molsysviewer as msv
from molsysviewer_molsysmt import get_addon, lifecycle, on_enable
from molsysviewer_molsysmt.runtime import ensure_runtime

msv.addons.register(get_addon(), lifecycle=lifecycle)

view = msv.MolSysView()
view.load(ms)                       # ms is a molsysmt.MolSys object
ensure_runtime(view).molecular_system = ms
on_enable(view)
view.show()
```

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
