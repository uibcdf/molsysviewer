# Proposal: Zero-Copy Visual Rendering and Heterogeneous Interoperability for MolSysViewer

## Abstract

We propose establishing a comprehensive zero-copy visual rendering architecture and heterogeneous hardware-sharing pipeline for `molsysviewer`. By integrating WebGPU shared array buffers, shared OpenGL/WebGL contexts (`cl_khr_gl_sharing`), and direct vertex buffer updates (VBO stream-mapping via `gl.bufferSubData`), we aim to connect GPU compute results from `molsysmt` directly to the viewer's rendering pipeline. This removes all intermediate host-to-device and device-to-host CPU memory transfer bottlenecks, enabling real-time 60 FPS trajectory playback and dynamic surface generation for massive macromolecular systems ($>100,000$ atoms).

---

## 1. Zero-Copy Trajectory Stream & WebGL VBO In-Place Mapping

### Context & Problem
During dynamic trajectory playback (e.g., streaming coordinate frames from a Python simulation/analysis kernel to the WebGL canvas over WebSockets or shared channels), the viewer currently destroys and rebuilds representation meshes (Cartoon, Spacefill, Licorice) for every incoming frame. This triggers massive CPU-side geometry generation, blocks the main browser event loop, and introduces heavy garbage collection spikes, limiting performance to $<5$ FPS on moderately sized proteins.

### The Proposal
Implement a direct VBO (VertexBufferObject) stream-mapping pathway when topological invariants (atom count, bonds, representation options) remain unchanged:
1. **Topological Signature Matching**: Assert that the incoming coordinate array size matches the active representation's vertex layout.
2. **WebGL bufferSubData Stream**: Rather than recreating the mesh, directly upload the new coordinates into the active GPU vertex position buffer using `gl.bufferSubData` or WebGPU mapped storage buffers.
3. **Synergy with MolSysMT**: Seamlessly stream coordinate values from `molsysmt`'s protected read-only array views directly to the serialization bridge without CPU-side copies.

```typescript
// Proposed high-performance WebGL vertex buffer map pathway
export function updatePositionsInPlace(gl: WebGL2RenderingContext, buffer: WebGLBuffer, newCoords: Float32Array) {
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    // Overwrite only the position coordinate attributes in GPU memory
    gl.bufferSubData(gl.ARRAY_BUFFER, 0, newCoords);
    gl.bindBuffer(gl.ARRAY_BUFFER, null);
}
```

---

## 2. GPU Compute Shader Surface Generation (SASA / SES)

### Context & Problem
Generating smooth Solvent-Accessible Surfaces (SAS) or Solvent-Excluded Surfaces (SES) is extremely demanding. Currently, analytical CPU triangulation or CPU marching cubes are used. For large structures ($>10,000$ atoms), generating these meshes freezes the interface for several seconds.

### The Proposal
Offload SASA/SES triangulation entirely to GPU Compute Shaders:
1. **Grid Voxelization Pass**: Map the coordinates to a 3D grid represented by a 3D GPU Texture. Compute the distance fields from the atomic spheres.
2. **GPU Marching Cubes**: Run a secondary compute pass directly on the GPU to generate the surface coordinates and indices.
3. **Zero Host-to-Device Roundtrips**: Directly pipe the generated vertex/index buffers into the rendering pipeline, maintaining complete geometry in device memory.

---

## 3. Shader-Based Selection & Color Scaling Lookups

### Context & Problem
Interactions such as highlighting active selection sets or color-scaling atoms by physical properties (charge, fluctuation, B-factor) currently trigger geometry rebuilds.

### The Proposal
Decouple structural geometry from color representation using shader textures:
1. **Attribute Texture Mapping**: Upload a static integer buffer mapping each mesh vertex to its corresponding global atom/residue index.
2. **Dynamic Property Texture**: Write updated styling descriptors (RGB colors, transparency, highlight state) into a small 1D/2D GPU texture.
3. **Fragment Shader Lookup**: Look up styling colors inside the Fragment Shader using the vertex-to-atom index map. Selection scaling becomes an instantaneous, O(1) texture bind (taking $<0.05$ ms).

---

## 4. Double-Buffered GPU Trajectory Frame Interpolation

### Context & Problem
Streaming coordinates at 60 FPS from a remote Python server consumes significant network bandwidth and introduces micro-stuttering due to network jitter.

### The Proposal
Perform dynamic coordinate interpolation directly in the Vertex Shader:
1. **Double-Buffered VBOs**: Load two consecutive coordinate sets (Frame $K$ and Frame $K+1$) into active GPU vertex buffers.
2. **Vertex Shader LERP**: Pass a normalized interpolation progress scalar $t \in [0, 1]$ as a uniform. Let the GPU interpolate positions:
   $$\mathbf{P}_{\text{interpolated}} = (1 - t) \cdot \mathbf{P}_{K} + t \cdot \mathbf{P}_{K+1}$$
3. **Bandwidth Optimization**: The Python server streams frames at only 5–10 FPS. The viewer's GPU interpolates smooth 60 FPS transitions locally, masking network latency and delivering buttery-smooth animations.

---

## 5. WebGPU Zero-Copy Shared Memory Architectures

As the web visualization ecosystem shifts to WebGPU:
- **Shared Storage Buffers**: Leverage Web Workers with shared memory to map analytical arrays directly into WebGPU storage buffers.
- **Unified Pipeline**: Run molecular dynamics simulations (e.g. interactive MD) and visualization in a shared, zero-copy WebGPU memory space.

---

## 6. OpenCL and WebGL/WebGPU Heterogeneous Interoperability

To prevent redundant CPU-GPU roundtrips in environments where analytical solvers run on the GPU:
- **Direct Context Sharing**: Leverage `cl_khr_gl_sharing` to share OpenGL/WebGL context directly with PyOpenCL.
- **Zero Host Transfer**: In workflows where calculations (like pocket volume boundaries, dynamic interfaces, or hydrogen bond metrics) are computed on the GPU via PyOpenCL, the resulting coordinate buffers or scalar fields are shared *directly* with the WebGL/WebGPU rendering pipeline as shared texture/vertex buffers, completely bypassing host memory copies.
