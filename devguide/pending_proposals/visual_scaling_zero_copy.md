# Proposal: Visual Scaling and Zero-Copy Rendering for Large Complexes

## Abstract

We propose optimizing the rendering pipeline and the Python-to-TypeScript communication bridge in `molsysviewer` using zero-copy data transmission and in-place vertex buffer object (VBO) updates. This resolves visual lags when displaying large geometric shape sets (like thousands of spheres or Delaunay tetrahedra from TopoMT pocket analysis) and prevents Jupyter WebSocket saturation.

---

## The Problem

When visualizing molecular topography in TopoMT (such as using `representation='tetrahedra'` or `representation='cloud'`), the backend generates thousands of three-dimensional coordinate sets.

The main rendering bottlenecks are:
1. **WebSocket Network Congestion**: Sending each shape or sphere as an individual message floods Jupyter's channel, freezing the browser.
2. **Mol* Representation Rebuilds**: Mol* currently destroys and rebuilds representation meshes from scratch upon every coordinate change, blocking the main thread and causing severe stuttering during playback.

---

## Proposed Solution

Implement an in-place update pathway in the TypeScript viewer to support efficient trajectory rendering:
1. **Persistent GPU Vertex Buffers**: Build geometry nodes once and retain references to their underlying WebGL/WebGPU VertexBufferObjects (VBOs).
2. **In-place GPU Updates (`gl.bufferSubData`)**: Stream coordinates as a single binary payload, uploading them directly to the GPU buffer via `gl.bufferSubData` without rebuilding meshes.
3. **Binary typed array transfers**: Send coordinates as binary buffers (`Float32Array`) via `anywidget`, bypassing JSON encoding/decoding overhead.

---

## Benefits

* **Butter-Smooth Playback**: Renders large trajectory frames with complex topological shapes at 60 FPS.
* **Low Memory Footprint**: Bypasses browser garbage collection spikes by reusing GPU buffers.
* **Scalability**: Enables interactive visualization of massive macromolecular surfaces without crashing Jupyter.
```
