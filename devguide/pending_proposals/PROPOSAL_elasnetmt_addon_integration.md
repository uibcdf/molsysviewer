# PROPOSAL: Official Integration of `molsysviewer_elasnetmt` Add-on

## Problem Statement
While the core architecture for add-ons is implemented, the library currently lacks out-of-the-box integration with key scientific modules like Elastic Network Models (ENM) from the `elasnetmt` ecosystem. Users currently see an empty add-ons list, hiding one of the viewer's most powerful features.

## Proposed Changes

### 1. Formalize the `elasnetmt` Add-on Package
Ensure the external repository `uibcdf/molsysviewer_elasnetmt` follows the `AddonSpec` contract precisely, including:
- **Panel:** A side panel for ENM parameter selection (cutoff, spring constant).
- **Shapes:** Direct rendering of elastic links between nodes using `view.shapes.add_links`.
- **Tools:** A specific tool mode for selecting nodes and calculating local correlations.

### 2. Discovery and Auto-enablement
- Update `msv.addons.discover()` to ensure it correctly identifies the production module.
- Add a project-level configuration option to auto-enable `elasnetmt` if the dependency is detected.

### 3. Workflow Example
```python
import molsysviewer as msv
view = msv.MolSysView()
view.load('1CRN')

# If installed, this should be automatic or one-line:
view.addons.enable('elasnetmt')

# The UI now shows an "Elastic Network" panel.
```

## Benefits
- **Domain-Specific Power:** Transforms a general viewer into a specialized biophysical analysis tool.
- **Showcase Extension:** Serves as the primary example for other community-driven add-ons (TopoMT, PharmacophoreMT).
