# Repository structure
_Last updated: 2026-05-22_

Use this page as the repo map when you need to find code quickly.

## Top-level layout

- `pyproject.toml`
  - Python packaging metadata and versioning (`versioningit`).
  - Package data includes `viewer.js` and `.map`.
- `molsysviewer/`
  - Python package: public API, loaders, shapes, widget, and helpers.
- `molsysviewer/js/`
  - TypeScript + Mol* sources and Node toolchain.
  - Source of truth for the JS runtime is `molsysviewer/js/src/`.
- `devtools/`
  - Conda build recipes and environment definitions.
- `docs/`
  - Sphinx documentation (user + developer).
- `tests/`
  - Python test suite (unit + integration).
- `.github/`
  - CI workflows and automation.
- `sandbox/`
  - Notebooks and experiments (not used in CI).

## Python package (`molsysviewer/`)

Key modules

- `molsysviewer/viewer/`
  - `MolSysView` lives here as a modular package, inheriting from 8 specialized Mixins to keep the codebase elegant and highly maintainable:
    - `__init__.py` preserves the public import path `molsysviewer.viewer.MolSysView`.
    - `core.py` keeps the high-level facade orchestration and central class definition.
    - `regions.py` (Mixin) handles spatial regions and atom selection logic.
    - `panel_mode.py` (Mixin) manages sidebar panel states and dynamic workspace controls.
    - `load.py` (Mixin) orchestrates importing molecular systems and stylesheet configuration.
    - `visibility.py` (Mixin) controls whole, representation, and component-level visibility.
    - `scene.py` (Mixin) manages camera, snapshots, figures, and exports.
    - `molsysmt_interface.py` (Mixin) provides a dedicated interface layer for MolSysMT integration.
    - `state.py` (Mixin) synchronizes layout configurations and traits.
    - `interaction.py` (Mixin) manages click, hover, and reproducible signal callbacks.
    - `history.py` owns replayable message/history recording.
    - `export.py` owns HTML/export message assembly.
    - `scene_registry.py` owns non-structural scene objects and layer grouping.
    - `representations.py` and `presets.py` keep normalization logic out of the facade.
- `molsysviewer/widget.py`

  - AnyWidget wrapper, exports `viewer.js` as `_esm` and synced traits.
- `molsysviewer/new_view.py`
  - Convenience `new_view(...)` that creates or reuses a `MolSysView`.
  - Includes `load_mode` to choose between subsetting the system or loading all
    and creating a `selection` region.
- `molsysviewer/loaders/`
  - `load_molsysmt.py`: MolSysMT conversion and payload serialization.
- `molsysviewer/regions.py`, `molsysviewer/layers.py`, `molsysviewer/whole.py`
  - Region/layer/whole wrappers with tag management.
- `molsysviewer/shapes/`
  - Python shape APIs (spheres, pockets, blobs, tubes, ellipsoids, links,
    displacements, pharmacophore, triangles, tetrahedra).
- `molsysviewer/config/`
  - User defaults and optional user presets.
- `molsysviewer/thirds/`
  - Jupyter helpers for embedding HTML exports.
- `molsysviewer/data/h5msm/`
  - Demo systems for tests and examples.

## TypeScript runtime (`molsysviewer/js/`)

Key modules

- `molsysviewer/js/src/index.ts`
  - AnyWidget entrypoint and docs-lite boot.
  - Popup host wiring and on-canvas controls.
- `molsysviewer/js/src/managers/viewer-controller.ts`
  - Central dispatcher and plugin lifecycle.
- `molsysviewer/js/src/managers/handlers/`
  - Loader/state/shape/scene/trajectory handlers.
- `molsysviewer/js/src/plugin/structure.ts`
  - MolSys payload parsing into Mol* topology and trajectory.
- `molsysviewer/js/src/shapes/`
  - Mol* shape builders.
- `molsysviewer/js/src/ui/controls.ts`
  - Overlay controls and trajectory UI.
- `molsysviewer/js/src/popup/`
  - Popout logic and synchronization.

## Generated artifacts

- `molsysviewer/viewer.js` and `molsysviewer/viewer.js.map` are generated from
  `molsysviewer/js/src/` and must not be edited by hand.

## Legacy path mapping

Some older issue discussions refer to a `devguide/` directory.
That content is now centralized under `docs/content/developer/`.

- `devguide/DESIGN/*` → architecture/design pages under `docs/content/developer/`
- `devguide/PLANNING/*` → `docs/content/developer/roadmap.md`
