# Proposal: In-Place GPU Vertex Buffer Updates for Trajectory Playback

## Abstract

We propose optimizing the TypeScript/JavaScript frontend (`js/src/`) in `molsysviewer` to execute in-place updates of GPU vertex position buffers during coordinate replacements (`set_coordinates`). By avoiding complete representation reconstruction and scene-rebuilds in Mol*, we can reduce coordinate update latencies from ~360 ms to under 10 ms, enabling butter-smooth, real-time scientific trajectory rendering at 60 FPS.

---

## The Problem

Performance benchmarks highlight that coordinate updates (`set_coordinates`) are the single most expensive runtime operation in typical interactive viewer sessions:
* **Dialanine (22 atoms)**: ~232.06 ms mean latency.
* **Villin Trajectory (596 atoms)**: ~360.78 ms mean latency.

Under the current implementation, every time a new frame's coordinates are passed over the Python-JS WebSocket bridge, MolSysViewer processes them by tearing down the existing molecular representation meshes (such as Cartoon, Licorice, or Spacefill) and reconstructing them from scratch. 

This causes:
1. Significant CPU-side geometry computation overhead.
2. WebGL buffer reallocation and high garbage collection pressure.
3. Jarring visual stuttering during high-frequency trajectory playback.

---

## Proposed Solution

Based on internal analysis of the **Mol* source tree** (`src_molstar`), we propose utilizing Mol*'s native capacity to modify WebGL position buffers directly without changing the topology or tearing down representation nodes.

### 1. Topology Match Detection
When new coordinates arrive, the TS manager should verify topological parity (i.e. that the number of atoms and structural metadata has not changed):
```typescript
// js/src/managers/coordinates.ts
function shouldUpdateInPlace(currentStructure: Structure, newCoordinates: number[]): boolean {
    const currentAtomCount = currentStructure.elementCount;
    const newAtomCount = newCoordinates.length / 3;
    return currentAtomCount === newAtomCount;
}
```

### 2. Direct WebGL Vertex Array Modification
If the topology matches, bypass the standard `state.build().to(repr).update(...)` tree-rebuild pipeline. Instead, inject the new coordinates directly into the underlying WebGL vertex buffers using Mol*'s `StructureElement.Loci` coordinate updates or updating the `Renderable` coordinate buffers:
```typescript
import { Structure } from 'molstar/lib/mol-model/structure';
import { Task } from 'molstar/lib/mol-task';

export async function updatePositionsInPlace(structure: Structure, coords: Float32Array) {
    // 1. Update the positions array on the model/structure representation.
    const model = structure.models[0];
    const positions = model.atomicConformation.coordinates;
    
    // Copy new coordinates in-place (converting coordinates from Å to nanometers if required)
    positions.x.array.set(coords.subarray(0, positions.x.array.length));
    positions.y.array.set(coords.subarray(positions.x.array.length, 2 * positions.x.array.length));
    positions.z.array.set(coords.subarray(2 * positions.x.array.length, 3 * positions.x.array.length));

    // 2. Request a representation update with 'positions' or 'geometry' dirty flag
    // This tells Mol* to update the existing GPU vertex array buffer via gl.bufferSubData 
    // instead of rebuilding the mesh.
    for (const repr of structure.representations) {
        if (repr.markDirty) {
            repr.markDirty();
        }
    }
}
```

### 3. Progressive Fallback
If the topology changes (e.g., appending a ligand or loading a completely different molecular system), the system falls back automatically to the robust, full scene reconstruction.

---

## Benefits

* **Performance Boost**: Vertex buffer updates in WebGL take less than 5–10 ms, allowing smooth 60 FPS trajectory playback.
* **Low Memory Footprint**: Bypasses costly garbage collection spikes by reusing existing GPU mesh buffers.
* **Better User Experience**: Smooth transitions during dynamic simulations or interactive coordinate manipulations.
