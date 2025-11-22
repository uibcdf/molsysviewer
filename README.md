# MolSysViewer

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/137937243.svg)](https://zenodo.org/badge/latestdoi/137937243)
[![](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/) 
[![Documentation](https://github.com/uibcdf/molsysviewer/actions/workflows/sphinx_docs_to_gh_pages.yaml/badge.svg)](https://github.com/uibcdf/molsysviewer/actions/workflows/sphinx_docs_to_gh_pages.yaml)
[![CI](https://github.com/uibcdf/molsysviewer/actions/workflows/CI.yaml/badge.svg)](https://github.com/uibcdf/molsysviewer/actions/workflows/CI.yaml)
[![codecov](https://codecov.io/github/uibcdf/molsysviewer/graph/badge.svg?token=9ZMA4YZLOR)](https://codecov.io/github/uibcdf/molsysviewer)
[![Install with conda](https://img.shields.io/badge/Install%20with-conda-brightgreen.svg)](https://conda.anaconda.org/uibcdf/molsysviewer)
[![Installation on ubuntu-latest](https://github.com/uibcdf/molsysviewer/actions/workflows/install_ubuntu_latest.yaml/badge.svg)](https://github.com/uibcdf/molsysviewer/actions/workflows/install_ubuntu_latest.yaml)
[![Installation on macos-latest](https://github.com/uibcdf/molsysviewer/actions/workflows/install_macos_latest.yaml/badge.svg)](https://github.com/uibcdf/molsysviewer/actions/workflows/install_macos_latest.yaml)

*A Mol\*-powered interactive viewer for molecular systems and trajectories,
designed for general use and for seamless integration with the MolSys
ecosystem.*

MolSysViewer is a modern molecular visualization tool built on top of the
[Mol\*](https://molstar.org) engine and exposed through a clean Python API.
It provides high-quality, interactive 3D rendering of molecular structures,
custom shapes, trajectories, and scientific overlays — directly inside Jupyter
notebooks and JupyterLab.

The viewer is implemented as a lightweight anywidget extension with a
TypeScript/Mol* core, giving it excellent performance, portability, and
extensibility while keeping the Python-facing API simple and intuitive.

MolSysViewer is developed as an independent library, and at the same time it
serves as the visualization engine for the **UIBCDF** ecosystem, integrating
naturally with tools such as:

- **MolSysMT** (molecular systems)
- **TopoMT** (cavity and topography analysis)
- **PharmacophoreMT** (pharmacophore modelling)
- **ElasNetMT** (elastic network models)
- and future modules of the MolSys family.

---

## ✨ Features

### ✔ Interactive molecular visualization
- Load PDB and mmCIF strings directly (“in-memory structures”)
- Load native MolSysMT systems without intermediate PDB conversion
- Load structures from remote URLs
- High-quality Mol\* rendering with cartoon, surface, and atomic styles
- Smooth camera, lighting, and interactivity

### ✔ Python → Mol* shape API
Scientific overlays can be rendered using a small and extensible Python API:

- `add_sphere(center, radius, color, alpha)`
- `add_spheres(centers, radius, ...)` (vectorized)
- Fully customizable transparency and visual parameters

Additional primitives (arrows, cylinders, billboards, meshes, labels) are part
of the active roadmap.

### ✔ Clean, modern architecture
- Built entirely on **anywidget** (no JupyterLab extension required)
- TypeScript + esbuild bundling
- Zero external CDN dependencies
- Viewer initializes reliably through a robust JS → Python handshake
- Fully self-contained for conda and pip packaging

### ✔ Designed for scientific workflows
In addition to being a general-purpose molecular viewer, MolSysViewer is
designed to support:

- cavity and pocket visualizations (TopoMT)
- pharmacophoric elements (PharmacophoreMT)
- trajectory inspection (MolSysMT)
- structure + annotation blends (ML predictions, scoring fields, etc.)

---

## 🚀 Example

```python
import molsysviewer as mv

pdb_text = """ATOM      1  N   MET A   1      11.104  13.207   8.551  1.00 20.00           N
ATOM      2  CA  MET A   1      12.560  13.329   8.276  1.00 20.00           C
ATOM      3  C   MET A   1      13.189  11.956   8.001  1.00 20.00           C
ATOM      4  O   MET A   1      12.589  10.935   8.353  1.00 20.00           O
END
"""

v = mv.MolSysView()
v.show()
v.load_pdb_string(pdb_text)

# Add a transparent sphere overlay
v.add_sphere(center=(12.0, 12.0, 8.0), radius=3.0, color=0x00ff00, alpha=0.4)
```

---

## 📦 Installation

MolSysViewer is available via **conda** (recommended):

```bash
conda install molsysviewer -c uibcdf
```

Or via **pip**:

```bash
pip install molsysviewer
```

To use the viewer inside Jupyter, make sure you have:

```bash
pip install anywidget
```

or the equivalent conda package.

---

## 🔧 Development

MolSysViewer uses:

- **Python** for the API and widget interface  
- **TypeScript + Mol\*** for rendering  
- **esbuild** for bundling the widget
- **anywidget** as the Jupyter integration layer

The JS bundle (`viewer.js`) is generated automatically during packaging and is
tracked in the repository (it carries the `@generated` banner) so that users of
the published wheels/conda packages never need a Node.js toolchain. The bundle
should not be edited by hand; rebuild it from the TypeScript sources under
`js/src/` instead.

Build the JS bundle manually for development:

```bash
cd js
npm install
npm run build
```

Then install the Python package:

```bash
pip install -e .
```

---

## 🛠 Project Status

MolSysViewer has reached a stable architectural foundation:

- robust Mol\* initialization  
- reliable Python ↔ JS message handling  
- stable sphere API  
- clean separation of Python/TS codebases  
- reproducible conda packaging with automatic JS build  

The library is now ready for rapid expansion toward advanced scientific
visualizations.

---

## 📍 Roadmap (short version)

- Additional geometric primitives (arrows, cylinders, labels, billboards)
- Tag-based scene management (`viewer.clear(tag=...)`)
- Camera helper utilities
- Alpha-sphere and pocket rendering (TopoMΤ)
- Pharmacophoric features
- Trajectory visualization (MolSysMT)
- Event callbacks (click, hover)
- Scene export

For the complete roadmap, see `ROADMAP.md`.

---

## 🤝 Contributing

Contributions are welcome! Whether you're interested in TypeScript/Mol\* 
development, Python API design, scientific visualization, or improving 
documentation, feel free to open an issue or pull request.

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 🧬 Acknowledgements

MolSysViewer uses the Mol\* engine developed by the Mol\* team and RCSB PDB.  
It is part of the **UIBCDF MolSys ecosystem** for molecular modeling, drug
design, structural analysis, and scientific computing.
