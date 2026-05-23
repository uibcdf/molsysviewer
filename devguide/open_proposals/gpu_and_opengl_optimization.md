# Proposal: High-Performance GPU and WebGL/WebGPU Optimization for Real-Time Molecular Visualization

## Abstract

We propose establishing a comprehensive GPU and WebGL/WebGPU optimization roadmap for `molsysviewer`. By migrating heavy geometric computations, trajectory streaming pipelines, and molecular selections from CPU-bound JavaScript to GPU-bound shaders (and utilizing the zero-copy read-only view architectures established in `molsysmt`), we aim to scale rendering performance to support real-time 60 FPS trajectory playback of massive molecular systems ($>100,000$ atoms) without garbage collection spikes or interface stuttering.

---

## 1. Zero-Copy Trajectory Stream & WebGL Vertex Buffer Updates

### The Problem
During dynamic trajectory playback (e.g., streaming coordinate frames from a Python simulation kernel to the WebGL frontend over a WebSocket), `molsysviewer` currently tears down and reconstructs the molecular representation meshes (Cartoon, Spacefill, Licorice) for every single frame. This causes massive CPU-side geometry computation overhead, heavy garbage collection pressure, and locks the render thread, limiting frame rates to $<5$ FPS on moderate systems (e.g. Villin headpiece, 596 atoms).

### The Proposal
Integrate an in-place vertex buffer update mechanism that bypasses representation rebuilding when topological parity is preserved:
1. **Topological Invariant Matching**: Verify that the incoming coordinate array size matches the active WebGL representation vertex buffer layout.
2. **Direct GPU Memory Sub-Data Upload**: Instead of rebuilding the mesh representation, update the existing GPU vertex position buffers in-place using WebGL's `gl.bufferSubData` or modern WebGPU mapping techniques.
3. **Synergy with MolSysMT**: Directly pipe `molsysmt`'s protected read-only coordinate views into the serialization bridge, eliminating CPU-side memory copies on both the Python host and the JS client.

```typescript
// Proposed high-performance WebGL position update path
export function updatePositionsInPlace(gl: WebGL2RenderingContext, buffer: WebGLBuffer, newCoords: Float32Array) {
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    // Directly stream position data to GPU VBO without modifying vertex attributes or index arrays
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, newCoords);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
}
```

---

## 2. GPU-Accelerated Mesh Generation (Solvent-Excluded and Accessible Surfaces)

### The Problem
Generating smooth Solvent-Excluded Surfaces (SES) or Solvent-Accessible Surfaces (SAS) is a highly expensive computation. Currently, the viewer relies on CPU-bound marching cubes or analytical triangulation. For larger proteins ($>10,000$ atoms), generating these surfaces blocks the browser main thread for several seconds, leading to a poor user experience.

### The Proposal
Offload surface mesh generation entirely to GPU Compute Shaders:
1. **Voxelization Compute Pass**: Map the atom positions to a 3D grid represented by a GPU 3D Texture. Run a compute shader to calculate distance fields from the atomic spheres.
2. **GPU Marching Cubes / Dual Contouring**: Run a secondary compute pass directly on the GPU to generate the surface vertex coordinates and indices.
3. **Zero Host-to-Device Roundtrips**: Feed the generated vertex buffer directly into the WebGL/WebGPU rendering pipeline, keeping the geometry entirely in device memory.

---

## 3. Shader-Based Dynamics Selection & Styling Mapping

### The Problem
User interactions such as selecting active residues, highlighting binding pockets, or coloring atoms by physical descriptors (like B-factor, charge, or RMSD fluctuations) currently trigger complete representation redraws, causing noticeable rendering stutters.

### The Proposal
Implement a shader-based styling architecture that decouples structural geometry from visual styles:
1. **Attribute Texture Mapping**: Upload an integer representation mapping each vertex to its corresponding atom/residue index in a static GPU buffer.
2. **Dynamic Descriptor Textures**: When selection states or styling descriptors change, write the new properties (e.g., RGB colors, alpha transparency, outline states) into a small 1D GPU texture.
3. **Fragment Shader Lookup**: Look up styling colors and visibility parameters inside the Fragment Shader using the vertex-to-atom map. Updating selections or color scales becomes an instantaneous O(1) texture bind, running at 0.05 ms latency regardless of the system size.

---

## 4. GPU-Side Trajectory Frame Interpolation

### The Problem
Streaming high-frequency trajectory coordinate frames (e.g. 60 FPS) from a remote Python server to a web browser consumes significant network bandwidth and introduces stutter due to network jitter.

### The Proposal
Offload trajectory frame interpolation to the GPU:
1. **Double-Buffered Coordinates**: Keep two consecutive frames (Frame $K$ and Frame $K+1$) active in GPU vertex buffers.
2. **Vertex Shader LERP**: Pass a normalized interpolation progress scalar $t \in [0, 1]$ as a uniform to the vertex shader. Let the GPU interpolate positions dynamically:
   $$\mathbf{P}_{\text{interpolated}} = (1 - t) \cdot \mathbf{P}_{K} + t \cdot \mathbf{P}_{K+1}$$
3. **Bandwidth Savings**: The Python backend only needs to stream coordinate frames at 5 or 10 FPS. The viewer's GPU interpolates smooth 60 FPS transitions locally, masking network latency and delivering buttery-smooth animations.

---

## 5. WebGPU Zero-Copy Shared Memory architectures (Post-1.0.0)

As the scientific visualization ecosystem transitions to WebGPU:
- **Shared Array Buffers**: Leverage zero-copy shared memory systems in multi-threaded Web Workers to stream coordinate arrays directly to WebGPU storage buffers.
- **Compute-to-Render Pipeline**: Fully align `molsysviewer` with high-performance WebGPU compute pipelines, enabling real-time physics simulations (e.g., interactive molecular dynamics) and rendering to run in a unified, zero-copy GPU memory space.

---

## 6. OpenCL and WebGL/WebGPU Heterogeneous Interoperability

To prevent duplicate CPU-GPU transfers in heterogeneous environments where scientific analytical solvers run on the GPU:
- **Shared OpenGL Contexts via PyOpenCL / WebCL**: Support context sharing using the `cl_khr_gl_sharing` OpenCL extension. In workflows where calculations (such as dynamic pocket searches or hydrogen bond metrics) are computed on the GPU via PyOpenCL, the resulting coordinate buffers or scalar fields are shared *directly* with the WebGL/WebGPU rendering pipeline as shared texture/vertex buffers, completely bypassing host (CPU) memory roundtrips.
- **Uniform API Invariants**: Align coordinates representations in `molsysviewer` with OpenCL memory buffers, allowing immediate rendering of GPU-computed spatial properties (such as pocket volume vertices).

