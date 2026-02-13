# Development Roadmap

This document outlines the strategic directions for **MolSysViewer** based on the 2026 technical audit and the project's long-term vision. The goal is to evolve from a visualization widget into an interactive analysis tool integrated with the UIBCDF ecosystem.

## Phase 1: Bi-directional Interactivity (High Priority)

Currently, communication is primarily one-way (Python → JS). We need to empower Python to react to user actions in the 3D canvas.

- **Picking System**: Implement atom/residue picking in the TypeScript layer.
- **Event Synchronization**: 
  - Emit `atom_clicked` or `selection_changed` messages from JS.
  - Create a callback system in Python (e.g., `view.on_click(func)`) to handle these events using MolSysMT indices.
- **Hover Feedback**: Support custom tooltips triggered from Python to show property values on mouse-over.

## Phase 2: Scientific Data Mapping & Primitives

Move beyond simple spheres into data-driven visualization and rich geometric support.

- **Geometric Expansion**: Implement official support for:
  - Arrows and Displacement Vectors (ElasNetMT).
  - Cylinders and Bonds customization.
  - Labels and Billboards for annotation.
  - General meshes for custom surfaces.
- **Color by Property**: Implement `view.color_by(values=array, colormap='viridis', selection='...')` to automatically map scientific data to the 3D model.
- **Domain-Specific Visuals**:
  - **TopoMT**: Dedicated rendering for pockets, cavities, and alpha-sphere sets.
  - **PharmacophoreMT**: Standardized features (points, spheres with orientation).

## Phase 3: Frontend Quality and Robustness

As the TypeScript layer grows in complexity, we must ensure it is as stable as the Python backend.

- **JS Testing Infrastructure**: Implement unit tests in `molsysviewer/js/tests/unit` (Vitest) and E2E tests in `molsysviewer/js/tests/e2e` (Playwright).
- **Message Validation in TS**: Implement schema validation for incoming messages from Python to catch protocol mismatches early.

## Phase 4: User Experience (UX) & Workflow

- **On-Canvas GUI**: Add a lightweight floating UI in the viewer to control layer visibility, transparency, and trajectory playback without re-executing Python cells.
- **Camera Helpers**: Add high-level API methods for common camera moves (align to axis, focus on ligand, fly-by).
- **Scene Persistence**: Ability to export/import the full viewer state (including shapes and camera) as a JSON bundle.

## Technical Debt

- **Zero Warnings Goal**: Reach 100% ArgDigest coverage for all arguments in the `shapes/` and `loaders/` submodules to eliminate `DigestNotDigestedWarning` during tests.
- **Numba Cache Management**: Ensure environment-safe Numba caching to avoid collision in shared HPC environments.
