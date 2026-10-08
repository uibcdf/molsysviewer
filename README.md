# MolSysViewer

[![MolSysSuite: Scientific Component](https://img.shields.io/badge/MolSysSuite-scientific%20component-0b7285?labelColor=24292f)](https://github.com/uibcdf/molsyssuite/blob/main/devguide/repository_badges.md#scientific-component)
[![MolSysSuite policy](https://github.com/uibcdf/molsysviewer/actions/workflows/molsyssuite-policy.yml/badge.svg?branch=main)](https://github.com/uibcdf/molsysviewer/actions/workflows/molsyssuite-policy.yml)
[![Python 3.11 | 3.12 | 3.13](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://github.com/uibcdf/molsyssuite/blob/main/devguide/python_policy.md)
[![License](https://img.shields.io/github/license/uibcdf/molsysviewer)](https://github.com/uibcdf/molsysviewer/blob/main/LICENSE)
[![Tests](https://github.com/uibcdf/molsysviewer/actions/workflows/CI.yaml/badge.svg?branch=main)](https://github.com/uibcdf/molsysviewer/actions/workflows/CI.yaml)
[![Codecov](https://codecov.io/gh/uibcdf/molsysviewer/branch/main/graph/badge.svg)](https://app.codecov.io/gh/uibcdf/molsysviewer)
[![Documentation](https://github.com/uibcdf/molsysviewer/actions/workflows/sphinx_docs_to_gh_pages.yaml/badge.svg)](https://www.uibcdf.org/molsysviewer/)
[![GitHub release](https://img.shields.io/github/v/release/uibcdf/molsysviewer)](https://github.com/uibcdf/molsysviewer/releases/latest)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18072956.svg)](https://doi.org/10.5281/zenodo.18072956)
[![Conda](https://img.shields.io/conda/vn/uibcdf/molsysviewer)](https://anaconda.org/uibcdf/molsysviewer)

Coverage: Python tests plus JavaScript unit tests, uploaded by the Linux/Python 3.13 CI lane on eligible full runs; weekly and conditional nightly recovery retain the existing cadence. This report does not cover all browser, GUI or GPU behavior. The badge reflects the last uploaded report, which may lag later direct or skip-CI commits; it does not certify a full matrix or scientific correctness.

*A Mol\*-powered interactive molecular viewer for Jupyter, built around the idea that
exploratory science should become reproducible science.*

MolSysViewer is a modern 3D molecular visualisation tool built on the
[Mol\*](https://molstar.org) engine and exposed through a clean Python API.
It renders structures, trajectories, and scientific overlays directly inside
Jupyter notebooks and JupyterLab — and it is designed so that every meaningful
thing you do interactively can be captured as replayable, exportable Python state.

Documentation: https://www.uibcdf.org/molsysviewer

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
view.save_state("scene-state.json")

# later, on another machine, or as a paper's supplementary material
restored = msv.demo["1TCD"]
restored.load_state("scene-state.json")
```

`restored` now carries the same regions, colours, representations, visibility and
overlays as the view you had been clicking around in. That round trip — not the
feature list below — is what MolSysViewer is for. The file stores scene state,
not the molecular system itself, so load the same or a compatible structure
before calling `load_state()`.

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
- `view.export.html(...)` — portable interactive HTML (self-contained or CDN-lite)
- `view.export.figure(...)` — publication-quality PNG/SVG snapshots
- `view.export.figure_publication_set(...)` — full light/dark/transparent bundle
- `view.movie.export(...)` — animated GIF or MP4 from trajectory frames
- State serialisation: `view.export_state()` / `view.import_state()`

### Addon system
MolSysViewer has a first-class addon API that lets external packages add
workspaces, panels, context actions, and shape providers without modifying the core:

Optional MolSysSuite integrations are owned and distributed by their toolkit.
Availability depends on the toolkit version; follow its installation instructions.
The table below lists module names known to the host, including a legacy module.

| Import as | Shipped by | What it adds | Maturity |
|---|---|---|---|
| `molsysviewer_molsysmt` | MolSysMT | Legacy addon module name retained for explicit discovery; ordinary workflows use the core API | alpha |
| `molsysviewer_topomt` | TopoMT | Pocket detection and topography visualisation | undeclared |
| `molsysviewer_elastnetmt` | ElastNetMT | GNM/ANM elastic network modes and contact network overlays | skeleton |
| `molsysviewer_pharmacophoremt` | PharmacophoresMT | Structure-based pharmacophore glyph overlays | skeleton |

**Maturity is what each add-on declares about itself**, so the column reports rather than
grades. The shared vocabulary is two words — `experimental` and `stable` — defined in
[`devguide/archive/addon_maturity_and_ownership.md`](devguide/archive/addon_maturity_and_ownership.md);
the values above predate it, and each toolkit adopts it when it re-declares. Until then,
read both `skeleton` and `alpha` as `experimental`, and `undeclared` as exactly that.

MolSysMT is a required backend of MolSysViewer. Loading, selection and interaction
calculations use it through the core API; you do not need a MolSysMT addon. The table
records known optional and legacy module names, not a guarantee that each toolkit
currently distributes or qualifies its integration. **None of them is production-ready
today.** Discover optional addons explicitly when their toolkit provides them.

### Canvas UX modes
- `controls_mode="minimal"` — 3-icon cluster + keyboard shortcuts (N/W/H)
- `panel_mode_style="floating"` — centred overlay panel, no viewport shift

---

## Installation

Install the published package with Conda:

```bash
conda create -n molsysviewer-env -c uibcdf -c conda-forge -c ambermd \
    python=3.14 molsysviewer jupyterlab
conda activate molsysviewer-env
jupyter lab
```

Conda installs the required MolSysMT backend and widget dependencies. The public
installation route is Conda; MolSysViewer is not distributed through PyPI.
An editable source installation is a developer workflow with its dependencies
already provisioned, as described below.

| Capability | Platform and Python scope |
| --- | --- |
| Core Python API, Jupyter widget and interactive HTML | Linux x86_64/ARM64, macOS Apple Silicon, Windows x86_64; Python 3.11–3.14 |
| Local standalone launchers and Qt desktop host | Experimental for 1.0; native Qt dependencies and visible rendering require separate qualification |
| Remote sessions | Unsupported preview; supported workflows remain post-1.0 |

Viewer 0.24.0 build 1 and MolSysMT 0.23.0 build 0 passed all sixteen public
installed platform/Python cells. The three Windows console commands are present
and their `--help` checks pass; this repairs the missing launchers in the older
0.23.4 package ([#101](https://github.com/uibcdf/molsysviewer/issues/101)).
Command availability does not certify the experimental desktop or remote host.

Central Python 3.14 admission remains pending under
[#93](https://github.com/uibcdf/molsysviewer/issues/93); the installed results
above do not declare that administrative admission. Intel-based macOS is outside
the current matrix. For experimental Qt work,
see the [separate development recipe](devguide/standalone_supported_environment.md).
That recipe preserves Linux transport evidence and Windows/macOS solver-only
observations; neither a successful solve nor the core noarch package certifies
native Qt rendering. Interactive HTML export remains a supported output.

---

## Development

MolSysViewer uses Python for the API and widget layer, TypeScript + Mol\* for
rendering, and esbuild for bundling.  The JS bundle (`viewer.js`) is tracked in
the repository and ships inside the wheel/conda package so that users never need
a Node.js toolchain.

```bash
# Use the provisioned suite development environment
conda activate molsyssuite@uibcdf_3.14
python -m pip install --no-deps -e .

# Rebuild the JS bundle (only needed when editing TypeScript sources)
cd molsysviewer/js
npm install
npm run build:runtime
cd ../..

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

## Citation

Use the stable concept DOI [10.5281/zenodo.18072956](https://doi.org/10.5281/zenodo.18072956)
when citing MolSysViewer generally. For reproducible work, cite the distinct version DOI
shown by Zenodo for the exact release you used. GitHub also renders the repository's
`CITATION.cff` through **Cite this repository**.

---

## License

MIT License.

MolSysViewer uses the [Mol\*](https://molstar.org) engine developed by the Mol\* team and RCSB PDB.
