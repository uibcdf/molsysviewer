# Proposal: Advanced Visualization Representations for Pockets, Voids, Channels, Interfaces, and Dry Components

## Abstract

We propose a comprehensive visualization design system for molecular topography features in `topomt` and `molsysviewer`. By integrating and adapting representation paradigms from leading platforms (such as CASTp's mouth caps, fpocket's chemical spheres, Caver/MOLE's variable-diameter tubes, HOLE's stacked ring profiles, and P2Rank's surface heatmaps), we aim to provide researchers with a rich visual toolkit to inspect, analyze, and communicate molecular cavity physics.

---

## 1. Wet Components: Pockets and Voids

### 1.1. Pocket Envelopes & Mouth Caps (CASTp Style)
Instead of rendering pockets as raw disjoint tetrahedra, this representation builds a continuous boundary envelope:
*   **Cavity Wall Mesh**: Renders a partial Solvent-Excluded Surface (SES) covering only the pocket-lining atoms. The mesh is bicolored: a warm/saturated color on the inner wall (facing the pocket) and a neutral color on the outer wall (facing the protein interior) to provide depth contrast.
*   **Translucent Mouth Caps**: Traces the boundary faces bordering the external solvent (`OCEAN`) and triangulates them into flat or slightly curved translucent "caps" or "lids" spanning the mouth portal.
*   **Scientific Value**: Clearly separates the interior chamber from the exterior gateway, showing exactly where a ligand enters the pocket.

### 1.2. Wireframe Density Isosurfaces (SurfNet Style)
An alternative to solid volumetric meshes which can block the view of internal ligands or critical residues:
*   **Contour Grid Wireframe**: Computes a volumetric density grid around the pocket's residence spheres and renders it as a clean wireframe isosurface.
*   **Scientific Value**: Provides a transparent envelope showing the overall pocket volume while keeping the pocket-bound ligand and surrounding side chains completely visible.

### 1.3. Chemical Affinity Spheres (fpocket Style)
Instead of painting all residence spheres with a single uniform color:
*   **Local Property Mapping**: Analyzes the physicochemical environment of the atoms lining each residence sphere.
*   **Affinity Color-Coding**: Colors spheres individually:
    *   **Yellow**: Hydrophobic surroundings (favorable for drug binding).
    *   **Blue**: Polar/charged hydrogen-bond acceptors/donors.
    *   **Red/Blue**: Specific electrostatic charges.
*   **Scientific Value**: Creates a visual pharmacophore/druggability map directly within the cavity volume.

### 1.4. Automated Transparency & Slicing for Voids
Voids are entirely encapsulated inside the protein volume and remain hidden under standard Cartoon or Spacefill representations.
*   **Automatic Focus & Clip**: When a void component is displayed, the viewer automatically calculates a dynamic clipping plane (slice) intersecting the void center, or sets the adjacent molecular representations to semi-transparent.
*   **Scientific Value**: Exposes internal cavities immediately without requiring manual camera clipping and transparency adjustments by the user.

---


## 2. Channels and Tunnels

### 2.1. Variable-Diameter Pipe Meshes (Caver/MOLE Style)
Renders the transport pathway as a continuous 3D tube:
*   **Clearance-Bounded Geometry**: The tube's centerline is determined by the Delaunay flow network path, and the tube's radius at each point dynamically matches the local clearance radius ($R_{\text{gate}}$ or $R_{\text{residence}}$).
*   **Bottleneck Highlighting**: The absolute narrowest point of the path (the gate controlling access) is highlighted with a bright red ring or a sphere of the corresponding gate radius.
*   **Scientific Value**: Visually reveals transport bottlenecks and internal chambers in a single, intuitive 3D shape.

### 2.2. Stacked Rings Profile (HOLE Style)
For pores and ion channels where seeing through the channel is crucial:
*   **Orthogonal Stacked Rings**: Renders a series of 2D wireframe circles perpendicular to the channel axis.
*   **Color-Coded Clearance**:
    *   **Green**: Wide regions ($R > 1.15 \text{ \AA}$, admitting water molecules).
    *   **Yellow**: Tight constriction zones (water fits tightly or must de-solvate).
    *   **Red**: Closed bottlenecks ($R < 1.15 \text{ \AA}$).
*   **Scientific Value**: Provides a skeletal wire profile of the pore that does not obstruct the view of the ion-coordinating lining residues.

### 2.3. Flow Streamlines (Dynamic Transportation)
*   **Vector Particles**: Draws small animated arrows or particles flowing along the channel graph edges.
*   **Scientific Value**: Visually illustrates solvent or ion transport directions and the paths of least resistance through the protein.

---

## 3. Interfaces and Dry Components

### 3.1. Contact Separation Sheets
*   **Bicolored Boundary Surface**: Generates a smooth, continuous surface sheet interpolating the contact zone between two interacting macromolecular bodies (e.g., protein-protein or protein-nucleic acid interfaces). The side facing Chain A is colored with Chain A's palette, and the side facing Chain B is colored with Chain B's palette.
*   **Scientific Value**: Explicitly defines the spatial boundary and shape complementarity of the interaction interface.

### 3.2. Hydrophobic Scaffold (Dry Core Skeleton)
*   **Contact Network Cylinder Mesh**: Visualizes the inaccessible dry bank core as a structural scaffold. Renders dark, thick cylinders connecting the centers of mass of packed hydrophobic residues.
*   **Scientific Value**: Represents the mechanical "spine" or folding core that stabilizes the protein's tertiary structure.

### 3.3. Convexity Heatmaps (Ridges and Protrusions)
*   **Curvature Projection**: Rather than adding meshes, projects a topographic curvature heatmap directly onto the protein's molecular surface.
*   **Color Scale**: Maps valleys (concave pockets) to cold colors and ridges (convex protrusions/loops) to hot colors.
*   **Scientific Value**: Yields a clean, non-cluttered visual summary of the protein's surface shape features.

---

## 4. Triangulation Stability & Cosphericity Guard

To guarantee that 3D visual representations remain stable and reproducible across molecular dynamics frames or minor coordinate perturbations:
*   **Coordinate Perturbation**: Applies a tiny, deterministic, simulation-safe coordinate noise (e.g., $10^{-5} \text{ \AA}$) during the Delaunay triangulation stage to break artificial cospheric degeneracies in highly ordered structures (like helices or lattices).
*   **Sliver Filtering**: Automatically identifies and collapses near-flat boundary tetrahedra (slivers) that lack physical volume, preventing them from creating unstable, flickering "bridges" in the 3D meshes.
*   **Scientific Value**: Resolves triangulation flips, ensuring that pocket shapes and mouth boundaries do not fluctuate or jitter between identical/near-identical conformations.

---

## 5. Interactive 2D-3D Trajectory Synchronization (Dynamic Fluctuation Plots)

For trajectory-based pocket breathing and gating analyses:
*   **2D-3D Synchronized Widget**: Embeds an interactive 2D line plot (e.g., using matplotlib, bokeh, or bqplot) directly alongside the 3D MolSysViewer widget in Jupyter. The 2D plot displays pocket volume or gate radius fluctuations over time.
*   **Bidirectional Interactivity**: Clicking or hovering over a time point in the 2D plot instantly updates the 3D viewer to show the corresponding frame and highlights the pocket conformation.
*   **Event Overlay**: Automatically markers key pocket events (like birth, merge, split, or collapse) directly onto the 2D timeline.
*   **Scientific Value**: Accelerates trajectory exploration by letting the quantitative data (volume/clearance) guide visual inspection.

---

## 6. Proposed API & Parameter Integration

We propose extending the `representation` parameter in `show_dfnd_components` to support these modes:

```python
def show_dfnd_components(
    view,
    topography=None,
    *,
    representation: str = 'envelope',  # 'envelope', 'wire_contour', 'affinity_spheres', 'pipe', 'rings', 'contact_sheet', 'scaffold', 'heatmap'
    ...
)
```

The rendering pipelines will map these options to specialized Mol* geometry builders (using meshes, lines, spheres, and color-mapping attributes) via the Jupyter-anywidget bridge.
