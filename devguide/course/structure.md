# Proposed Course Structure: "Introduction to MolSysViewer"

This document outlines the 50-module comprehensive curriculum for the **MolSysViewer Master Course**. It is organized into a **Common Core** of 20 modules and **Four Specialized Paths** (Modules 21-50) that apply the viewer's capabilities to real-world biological and pharmaceutical challenges.

---

## 🏗️ Part 1: The Common Core (Modules 1-20)
*Goal: Master the fundamentals of molecular loading, visual aesthetics, trajectories, and programmatic scene composition.*

### Module 1: The Molecular Widget & Layouts
*   **Objective:** Initialize the viewer, personalize the UI, and control the workspace layout.
*   **Topics:** Widget rendering, `view.load()`, loading blocks, showing unit cells (`view.show_box()`), checking state with `view.info()`, and controlling the GUI layout using Panel Mode (`view.set_panel_mode()`) with dock/split options.
*   **Exercise:** Load a protein, personalize the background, display the unit cell, and switch the viewer into a split-screen workbench layout.

### Module 2: Talk to Atoms
*   **Objective:** Select structural subsets programmatically and inter-actively.
*   **Topics:** Mouse clicks, `active_selection`, saving selections (`view.selections.save()`), and MolSysMT selection query syntax (`backbone`, `sidechain`, `within`).
*   **Exercise:** Click a ligand, save the active selection, and query neighboring residues within 5 Å.

### Module 3: Visual Hierarchy
*   **Objective:** Master the anatomical hierarchy of the scene.
*   **Topics:** The global baseline (`view.whole`) vs. named subsets (`regions`). Creating regions (`view.new_region()`) and controlling visibility.
*   **Exercise:** Segment a protein-ligand system, naming the ligand as a distinct region, and hide the rest of the protein.

### Module 4: Automatic Segmentation
*   **Objective:** Reduce visual noise in multi-chain or complex assemblies.
*   **Topics:** Hierarchical segmentation (`view.make_regions_by('chain')`), and mass visibility control with `view.isolate()`.
*   **Exercise:** Load a dimer, segment it by chain, and isolate the dimer interface.

### Module 5: Manual Representations
*   **Objective:** Control the granular visual drawing of atoms and bonds.
*   **Topics:** Representation types (`cartoon`, `licorice`, `spacefill`), parameters (radii, detail), and transparency (`alpha`) on specific regions.
*   **Exercise:** Style a saved binding site as licorice and make the rest of the protein a transparent cartoon.

### Module 6: Presets & Smart Views
*   **Objective:** Apply high-level Mol* visual recipes.
*   **Topics:** Representations vs. Presets, built-in recipes (`atomic-detail`, `polymer-cartoon`), and loading custom `User Presets` from external YAML files.
*   **Exercise:** Load an external YAML preset and apply it to a complex system to render standard cartoon-and-stick representations.

### Module 7: Color as Information
*   **Objective:** Use color to represent structural or physical data.
*   **Topics:** Categorical schemes, quantitative gradients (`set_color_by_values()`), and mapping Matplotlib/continuous colormaps.
*   **Exercise:** Color a protein surface based on a list of residue-level conservation scores.

### Module 8: Spatial Camera
*   **Objective:** Master viewpoint navigation programmatically.
*   **Topics:** `view.camera.zoom()`, perspective vs. orthographic projections, and capturing/restoring camera `snapshots`.
*   **Exercise:** Find a pocket orientation, save a camera snapshot, move the camera, and programmatically return to it.

### Module 9: Textual Annotation
*   **Objective:** Enrich the 3D scene with labels.
*   **Topics:** Placing text labels at selection centers (`add_label()`), managing visibility, and remapping label positions.
*   **Exercise:** Build a guided tour of a protein by placing labels on key residues.

### Module 10: Precision Measurements
*   **Objective:** Extract quantitative geometric parameters safely.
*   **Topics:** Distance, angle, and dihedral measurements, naming registries, and unit-safety integration via `PyUnitWizard` (Å, degrees).
*   **Exercise:** Measure a catalytic distance and retrieve it as a physical quantity with units.

### Module 11: Abstract Shapes
*   **Objective:** Render non-atomic shapes to represent physical concepts.
*   **Topics:** The unified shapes manager (`view.shapes`), adding spheres (`add_sphere`), lines (`add_links`), and direction vectors.
*   **Exercise:** Add a transparent sphere at the center of mass of a pocket.

### Module 12: Layer Organization
*   **Objective:** Organize complex scenes into visibility groups.
*   **Topics:** Layers concept (`view.layers`), tagging objects and regions with `layer_tag`, and mass layer visibility toggling.
*   **Exercise:** Group pocket surfaces, measurements, and labels under an `active_site_layer` and toggle them simultaneously.

### Module 13: Time & Trajectories
*   **Objective:** Navigate time-resolved structure datasets.
*   **Topics:** Loading trajectories (`traj_chicken_villin_HP35_solvated.h5msm`), player controls (`view.player`), speed, looping, and index querying.
*   **Exercise:** Play a trajectory of a folding peptide and inspect the structure index at a specific folding milestone.

### Module 14: Sectioning & Clipping
*   **Objective:** Slice through dense molecular structures.
*   **Topics:** Camera-space clipping (`set_clip_planes`), world-space sectioning (`add_section`), and sectioning gizmos.
*   **Exercise:** Section a membrane protein model to reveal the internal ion channel pore.

### Module 15: Add-on Infrastructure
*   **Objective:** Expand the viewer's capabilities with specialized modules.
*   **Topics:** Add-on discovery (`msv.addons.available()`), workspace registration, and loading custom add-on panels.
*   **Exercise:** Enable a scientific add-on and inspect its specialized workspace.

### Module 16: Diagnostic Forensics
*   **Objective:** Debug viewer events and trace internal messages.
*   **Topics:** Telemetry signals, breadcrumbs, enabling JS debug log (`debug_js=True`), and auditing `view.js_logs`.
*   **Exercise:** Trigger a series of actions, capture the underlying Mol* messages, and inspect them.

### Module 17: The Python Backend
*   **Objective:** Leverage the MolSysMT computational engine.
*   **Topics:** The `view.molsys` property, running geometric analysis on the backend, and updating the visual scene.
*   **Exercise:** Count the number of water molecules using the backend and update a region's visibility based on this count.

### Module 18: Coordinate & Topological Engineering
*   **Objective:** Modify structural coordinates and topology dynamically, verifying visualization robustness.
*   **Topics:** `view.get_coordinates()`, pushing updates to the GPU with `view.set_coordinates()`, applying structural edits (removing residues or mutations), and verifying that annotations, shapes, and measurements survive through remapping.
*   **Exercise:** Rotate a domain programmatically, perform a structural deletion from Python, and verify that catalytic measurements survive the rebuild.

### Module 19: Scene Composition
*   **Objective:** Merge independent viewer sessions.
*   **Topics:** `msv.tools.basic.merge()`, remapping atom indices, and tag collision resolution.
*   **Exercise:** Combine a protein scene with an analysis scene into a single merged viewer.

### Module 20: Professional Shareables
*   **Objective:** Export high-quality outputs for publications.
*   **Topics:** Image rendering, `FigureSpec` style recipes, and exporting standalone interactive HTML files.
*   **Exercise:** Generate a publication-quality figure and export the session as a standalone HTML file.

---

## 🛣️ Part 2: The Crossroads & Specialized Paths (Modules 21-50)
*After completing the Common Core, students choose one of the following 4 paths to study advanced structural biology and drug design.*

### 🧬 Path A: Allostery and Collective Normal Modes
*   **System:** **Adenylate Kinase (AdK - PDB 4AKE/1AKE)**.
*   **Focus:** Conformational changes and collective dynamics driving lid domain transitions.
*   **Add-on:** `elasnetmt` (Elastic Networks).
*   **Topics (Modules 21-50):**
    *   Building the Elastic Network Model (ANM) on the open state.
    *   Rendering network bonds (`add_links()`) with thicknesses scaled by spring constants.
    *   Visualizing collective modes with direction vectors (`add_vectors()`).
    *   Tracing pocket fluctuation constraints in the closed state using anisotropy elipsoids (`add_anisotropy_ellipsoids()`).

### 🕳️ Path B: Druggable Cavities and Tunnels in Glycolysis Enzymes
*   **System:** **Triosephosphate Isomerase (*T. cruzi* - PDB 1TCD)**.
*   **Focus:** Active-site pockets and entry channels to block parasite glycolysis.
*   **Add-on:** `topomt` (Topology and Cavity Tools).
*   **Topics (Modules 21-50):**
    *   Topological pocket detection and loop 6 flexibility analysis.
    *   Visualizing druggable pocket volumes using Gaussian density fields (`add_pocket_blob()`).
    *   Rendering substrate entry tunnels using section-variable tubes (`add_channel_tube()`).
    *   Slicing the TIM barrel dimer with world-space sectioning (`add_section()`) to evaluate pocket accessibility.

### 🔬 Path C: Folding and Stabilisation in Complex MD Trajectories
*   **System:** **Chicken Villin Headpiece (HP35) Folding Trajectory**.
*   **Focus:** Characterizing physical folding, hydrophobic core collapse, and salt-bridge networks.
*   **Add-on:** None (Pure MolSysViewer).
*   **Topics (Modules 21-50):**
    *   Navigating key MD folding milestones (unfolded, intermediates, folded states).
    *   Mapping solvent accessibility (SASA) and thermal stability (RMSF) directly on the surface (`set_color_by_values()`).
    *   Visualizing aromatic stacking and hydrophobic core collapse over time.
    *   Inspecting dynamic covalent and non-covalent connectivity networks.

### 💊 Path D: Pharmacophore Dynamics in Druggable Cavities
*   **System:** **SARS-CoV-2 Main Protease (Mpro - PDB 6W9C) or HIV Protease (PDB 1HSG) with ligand**.
*   **Focus:** Evaluation of drug candidate binding stability and pharmacophoric fluctuations.
*   **Add-on:** `pharmacophoremt` (Pharmacophores).
*   **Topics (Modules 21-50):**
    *   Generating pharmacophore features (donors, acceptors, hydrophobic sites) on both the ligand and active-site residues.
    *   Rendering features as 3D rings and vectors (`add_pharmacophore_shapes()`) over the trajectory.
    *   Analyzing the stability and fluctuations of complementary pharmacophore alignments (ligand-receptor contacts).
    *   Characterizing unbinding pathways and water entry events.
