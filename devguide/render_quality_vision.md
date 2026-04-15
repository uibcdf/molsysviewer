# VISION: High-Fidelity Rendering and Blender Integration

> **Roadmap Status:** Strategic vision for **Post-1.0**. Focused on publication-grade aesthetics and cinematic production.

## Problem Statement
While Mol* (the current engine) provides excellent real-time performance and illustrative styles, it is limited by the constraints of WebGL for true photorealistic rendering. High-impact journal covers and professional outreach videos often require advanced features like:
- Physical-based raytracing (path tracing).
- Complex material properties (subsurface scattering, advanced glass/transparency).
- Cinematic depth of field and motion blur.

## Proposed Solutions

### 1. High-Performance GPU Rendering (Native)
Explore alternatives to WebGL to break current graphical limitations:
- **WebGPU Transition:** Investigate moving Mol* or a parallel renderer to WebGPU for native access to modern GPU features like compute shaders and improved raytracing kernels.
- **Qt/PySide6 Offscreen Rendering:** For the standalone mode, leverage Qt's ability to interface with high-end raytracing engines (like Intel OSPRay or NVIDIA OptiX) to generate publication-quality frames without a browser.

### 2. The Blender Bridge
Instead of reinventing a high-end renderer, MolSysViewer should leverage **Blender**, the industry-standard open-source 3D suite.
- **Direct Export to `.blend`:** Translate the MolSysViewer scene (structures, regions, shapes, and camera) into a Blender file.
- **"Blender Mode" in Jupyter Widget:** Explore the possibility of an interactive "Blender View" directly inside the notebook canvas. This could be achieved via:
    - A background Blender instance streaming frames to the widget.
    - Using Blender's Python API to update a high-fidelity viewport that mirrors the Mol* interactive state.

### 3. Molecular Materials Library
Provide a set of pre-configured shaders (e.g., "Frosted Protein", "Metallic DNA") that look consistent across both Mol* (approximate) and Blender (photorealistic).

## Benefits
- **Scientific Storytelling:** The "Blender Mode" would allow researchers to compose their cinematic scenes without leaving the Jupyter environment.
- **Unified Workflow:** One click to go from interactive exploration (Mol*) to high-fidelity production (Blender).
- **GPU Mastery:** Native GPU raytracing ensures that even without Blender, MolSysViewer remains a top-tier tool for scientific figures.

## Implementation Path
- Investigate the `MolecularNodes` Blender add-on as a potential backend.
- Research WebGPU support in Mol* and sibling projects.
- Prototype a "Headless Blender" worker that can receive scene messages from the MolSysViewer widget.
- Phase 1: Static `.blend` export.
- Phase 2: Integrated "Blender Mode" preview in the Jupyter widget.

