# Vision for v1.0: Styles, Architecture and User Experience

This document consolidates the design decisions and architectural vision for the **MolSysViewer 1.0** release, following the discussions held in March 2026.

## 1. The Core Leitmotiv: The 50/50 Split

MolSysViewer is built on a dual foundation, as defined in our guiding principles:
1.  **50% Visualizer**: Focus on beauty, communication, and "publication-quality" defaults. It must feel modern, "alive," and polished.
2.  **50% Analysis Tool**: Focus on scientific rigor, reproducibility, and deep integration with the Python data model (`molsysmt`). Exploration must result in replayable artifacts.

## 2. User Personas: Symmetry and Context

To achieve excellence, we design for two distinct but perfectly synchronized paths:

### 2.1 The Advanced User (Programmatic API)
- **Context**: Jupyter Notebooks, automated scripts, large-scale data analysis.
- **Requirement**: Total control over the scene, a predictable and hierarchical object model, and clear architecture.
- **Ideal**: An API where the user sees objects and collections (`view.regions`, `view.styles`, `view.selections`) and can manipulate them with high-level scientific intent.

### 2.2 The Canvas User (Interactive UX)
- **Context**: Real-time exploration, structural inspection, quick visual queries.
- **Requirement**: A lightweight, comfortable, and conceptually solid interface.
- **Ideal**: High-level tools (GroupPanel, Context Menus, Tool Banners) that perform complex scientific actions without exposing the underlying graphic engine's internal state.

**The Bridge**: The state is unified. An action in the API appears in the UI, and a measurement taken with the mouse is accessible via the Python API (`view.measurements.records()`).

---

## 3. The Evolution of Presets to "Styles"

### 3.1 From Computer Graphics to Scientific Intent
While Mol* uses "Presets" as macro-commands to setup representations, MolSysViewer evolves this into **Styles**.
- A **Style** is a "Visualization Recipe" that bridges data analysis and graphics.
- **Data-Driven**: Styles should be reactive to chemical properties (e.g., coloring a surface by partial charges fetched from `molsysmt`).
- **Compositional Model**:
    - **Scene Styles (Exclusive)**: Define the base look (Default, Dark, Atomic Detail) and reset the scene.
    - **Focus Styles (Cumulative)**: Add layers of meaning (e.g., `+ Hydrophobicity`, `+ H-Bonds`) over existing selections without clearing the base scene.

### 3.2 Structure of a Style Object
- **Declarative (Easy Path)**: A simple constructor for 80% of use cases (e.g., `Style(representation='surface', color='electrostatic')`).
- **Rule-Based (Advanced Path)**: Allows logic based on **chemical predicates** (e.g., "apply sticks if B-factor > X AND residue is Lysine").
- **Visual Narrative**: Styles must include scene-level parameters to ensure **publication-quality** results by default:
    - Lighting profiles (e.g., "illustrative", "ambient occlusion"),
    - Material properties (roughness, metalness),
    - desaturation of non-selected elements to create focus.
- **Transportable Artifacts**: Styles are designed to be exported to standard schemas (JSON/YAML). This allows researchers to share "Visual Standards" alongside their data, ensuring that "how it looks" is as reproducible as "what it is."

---

## 4. Architectural Decisions: Separation of Concerns

### 4.1 Navigation vs. Management (The "Map vs. Inventory" Argument)
- **GroupPanel (Navigation)**: Acting as the "Map." We intentionally chose **nested left-border lines** instead of full bounding boxes. 
    - *Argument*: Lines are "economically" cheaper in terms of screen real estate and less visually invasive, maintaining readability in narrow sidebars while still conveying hierarchy.
    - *Interaction*: We use **hover tooltips** on these markers to reveal metadata (Molecule/Component names) without taking up permanent space.
- **LayerPanel / State Inspector (Management)**: Acting as the "Inventory." A separate area for managing high-level artifacts (Regions, Measurements).

### 4.2 The "Selection -> Action" Flow
- **Pattern**: Selection (via GroupPanel or Canvas) $\rightarrow$ Action (via Context Menu or a dedicated **Action Bar**).
- *Decision*: We rejected placing action icons (like "Animate" or "Style") on every row of the `GroupStrip`. 
- *Rationale*: To avoid "clutter" and maintain a professional aesthetic. Actions should appear only when a subject (Selection) is defined.

---

## 5. Implementation Roadmap (Towards 1.0)

### 5.1 Tool Lifecycle and UX
- **Feedback**: Implement a status banner/overlay for active multi-pick tools (e.g., "Distance Measurement: Pick 1 of 2").
- **Cancellation**: Standardize the `Esc` key as the universal signal to terminate any active tool mode and clear partial states.

### 5.2 Hierarchy and Scaling
- **Collapsible Hierarchy**: Add the ability to collapse/expand Molecule and Component containers in the `GroupPanel` to handle large systems (e.g., thousands of water molecules) efficiently.

### 5.3 Workbench Tutorials
- Shift documentation from pure API reference to case-study-driven tutorials:
    - *Pocket Contact Analysis*: From identification to labeled distance measurements.
    - *Structural Mutation Replay*: How visual artifacts survive structural edits.

---

## 6. Summary of Decisions Taken (March 2026)

- **Hierarchical Navigation**: Implemented nested colored left-border lines for Molecule/Component visualization in `GroupStrip`.
- **Range Selection**: Adopted `Shift + Alt + click` as the standard for contiguous group selection, synchronized between Canvas and Strips.
- **Rebuild Robustness**: Fixed history recording bugs to ensure all artifacts (Labels, Measurements, Selections) survive structural `remove()`/`add()` operations through index remapping.
- **ArgDigest for Shapes**: Exhaustive Python-side validation for complex shape arguments (iso-levels, eigenvalues, tensors).
