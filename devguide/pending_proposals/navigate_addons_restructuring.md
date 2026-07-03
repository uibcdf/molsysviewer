# Proposal: Navigate and Add-ons Panel Restructuring

This document describes the design, rationale, and implementation plan for the restructuring of the **Navigate** and **Add-ons** (formerly **Workbench**) panels in MolSysViewer.

---

## 1. Rationale (Why)

Currently, the sidebar panels suffer from mixed responsibilities and suboptimal space utilization:
*   **Mixed Concerns**: Core viewer controls (like annotations, measurements, shapes, and scene settings) are housed under the "Workbench" panel alongside third-party analytical extensions (like `molsysmt`, `topomt`, etc.).
*   **Suboptimal Screen Real Estate**: In Add-ons mode, displaying a permanent list of other inactive add-ons in a narrow column eats up valuable width that could be used for navigating the sections of the active tool.
*   **Cognitive Friction**: The navigation model is inconsistent. Navigate uses a split of summarized cards on the left and sequence strips on the right, while Workbench uses expandable sections and a top-bar dropdown.

By reorganizing these panels, we establish a clean separation of concerns and a unified navigation paradigm:
*   **Navigate Panel** becomes the exclusive home for all native MolSysViewer controls (Structure, Selection, Regions, Shapes, Layers, and Scene).
*   **Add-ons Panel** becomes the host for third-party analytical and computational extensions.
*   **Unified Visual Paradigm**: Both panels adopt a dynamic **`[Left Sidebar (180px)] | [Right Content Area]`** layout, reducing cognitive load.

---

## 2. Design Specification (What)

### A. The Navigate Panel (Core View Controls)
The Navigate panel will display a permanent left sidebar with 6 navigation buttons acting as live badges/metrics. Selecting a button toggles the display of the corresponding subpanel in the right content area:

1.  **Structure** (Default)
    *   *Left badge*: e.g., `"2 chains, 22 res"`
    *   *Right content*: The existing sequence strips / chain sequence rulers (`GroupStrip`s).
2.  **Selection**
    *   *Left badge*: e.g., `"Active: 42 atoms"` or `"None"`, plus `"3 saved"`
    *   *Right content*:
        *   **Active Selection**: Displays the current atom count, hierarchy level, and buttons to **Clear Selection**, **Save Selection** (with tag input), or **Create Region** (with tag input).
        *   **Saved Selections**: A list of saved selections. Clicking a row activates it. Hovering shows a trash icon to delete it.
3.  **Regions**
    *   *Left badge*: e.g., `"4 regions"`
    *   *Right content*: A list of all created regions. For each region: name, atom count, and three quick actions: **Focus** (target icon), **Show/Hide** (eye icon), and **Delete** (trash icon).
4.  **Shapes**
    *   *Left badge*: e.g., `"3 shapes"`
    *   *Right content*: A list of custom 3D geometric shapes. For each shape: tag, shape type, and quick actions: **Show/Hide** (eye icon) and **Delete** (trash icon).
5.  **Layers**
    *   *Left badge*: e.g., `"2 layers"`
    *   *Right content*: A list of annotations (labels) and measurements (distance lines). For each layer: tag, kind, and quick actions: **Show/Hide** (eye icon) and **Delete** (trash icon).
6.  **Scene**
    *   *Left badge*: e.g., `"Dark · Spin"`
    *   *Right content*: General viewport and style settings:
        *   **Viewport**: Toggle Background Color (Light/Dark), Spin (auto-rotate), Swing (auto-oscillate).
        *   **Camera**: Camera Mode (Perspective/Orthographic), Fog intensity slider.
        *   **Figure Export**: Resolution scale, preset, and transparent background options.

---

### B. The Add-ons Panel (Extension Host)
The Add-ons panel adopts a dynamic layout based on whether a specific add-on workspace is selected:

#### State 1: Add-on Selector Screen (No active add-on workspace, `currentWorkspaceId = "core"`)
*   **Left Sidebar**: Hidden (`display: "none"`).
*   **Right Content Area** (takes 100% card width): A beautiful grid of cards representing all active add-ons (e.g. `molsysmt`, `topomt`).
    *   Each card displays the add-on name, description (e.g., *"TopoMT: cavity detection and channel analysis"*), and capability counts.
    *   If an add-on failed to load during Python initialization, its card shows a red warning badge. Clicking it reveals the diagnostic traceback.
    *   Clicking a valid card activates that add-on.

#### State 2: Active Add-on Workspace (An add-on is selected, e.g. `currentWorkspaceId = "molsysmt"`)
*   **Left Sidebar**: Visible (`display: "flex"`, width 180px).
    *   At the very top: An elegant **`← Back to Add-ons`** button to return to the Selector Screen.
    *   Below it: A vertical menu of the sections/panels of the active add-on (e.g. `basic`, `topology`, `structure`, `build`, `hbonds` for `molsysmt`).
*   **Right Content Area**: Renders the operations, tables, and custom interactive widgets of the selected section.

---

## 3. Implementation Plan (How)

### Step 1: Branch Creation
We will create a new git branch: `feature/navigate-panel-redesign`.

### Step 2: Codebase-wide Renaming (workbench -> addons)
To avoid future confusion and ensure full consistency between user interface and code names, we will perform a comprehensive rename of all `workbench` references to `addons` / `addon` across the codebase:
1.  **File Renaming**:
    *   `molsysviewer/js/src/ui/workbench-panel.ts` -> `molsysviewer/js/src/ui/addons-panel.ts`
2.  **TypeScript Class and Types Renaming**:
    *   `WorkbenchPanel` -> `AddonsPanel`
    *   `lastPanelMode: "navigate" | "workbench"` -> `lastPanelMode: "navigate" | "addons"`
    *   `workbenchAddons`, `workbenchAnnotations`, `workbenchMeasurements`, `workbenchShapes`, `workbenchScene` -> `addonsList`, `addonsAnnotations`, `addonsMeasurements`, `addonsShapes`, `addonsScene` (or similar)
3.  **Python API Renaming**:
    *   `AddonWorkbenchSectionSpec` -> `AddonSectionSpec`
    *   `workbench_sections` attribute in `AddonSpec` -> `addon_sections` (we can keep a deprecated alias property for backward compatibility if needed)
    *   `target_panel: "workbench"` option -> `target_panel: "addons"`
4.  **Message Payload / Event Names**:
    *   `panel: "workbench"` -> `panel: "addons"`
    *   Selectors like `data-molsysviewer-workbench-panel` -> `data-molsysviewer-addons-panel`

### Step 3: JS UI Refactoring
1.  **`GroupPanel` (`group-panel.ts`)**:
    *   Refactor constructor to create 6 right-side section containers (`structureSection`, `selectionSection`, etc.).
    *   Render left sidebar buttons as clickable tabs with live metric badges.
    *   Implement tab-switching logic by toggling `display` styles (`flex` vs `none`).
    *   Build DOM structures for the new tabs (Selection active/saved lists, Regions control lists, Shapes lists, Layers lists, and Scene controls).
2.  **`AddonsPanel` (`addons-panel.ts` - formerly `workbench-panel.ts`)**:
    *   Refactor layout to support a two-column structure when a workspace is active.
    *   Render the vertical sidebar menu of addon sections when `currentWorkspaceId !== "core"`.
    *   Render the `← Back to Add-ons` button.
    *   Hide the sidebar and expand the home catalog grid when `currentWorkspaceId === "core"`.
    *   Integrate diagnostic warnings directly into the catalog cards.
3.  **Top Bar UI**:
    *   Rename the user-facing button label from `"Workbench"` to `"Add-ons"`.

### Step 4: Event Routing and State Synchronization
1.  **Controller (`viewer-controller.ts`)**:
    *   Wired actions for `delete_selection`, `toggle_layer_visibility`, and resetting workspace to `"core"`.
    *   Ensure clicking the top-bar "Add-ons" tab when already inside an addon resets the active workspace back to `"core"`.
2.  **Python Core (`viewer/core.py`)**:
    *   Wired `delete_selection` and `toggle_layer_visibility` actions in `interaction_context_action` event handler.

### Step 5: Verification and Tests
*   Update unit and E2E tests in `tests/` to reflect new layout states and the `workbench` -> `addons` rename.
*   Run the full pytest suite (`pytest tests/`) to ensure no regressions are introduced.


---

## 4. Design Details and Testing Contracts

### A. E2E Selector Contracts (Data Attributes)
To ensure Playwright E2E and unit tests can select the new controls reliably, we define the following `data-*` attributes that will be injected into the DOM elements:

*   **Navigate Tabs (Left Column)**:
    *   `data-molsysviewer-group-panel-tab="[tab_id]"` where `tab_id` is one of `structure`, `selection`, `regions`, `shapes`, `layers`, `scene`.
*   **Active Navigate Tab Container**:
    *   `data-molsysviewer-group-panel-section="[tab_id]"`
*   **Add-on Selector Cards**:
    *   `data-molsysviewer-addon-card="[addon_id]"`
*   **Add-on Sections (Left Column)**:
    *   `data-molsysviewer-addon-section-tab="[section_id]"`
*   **Add-on Back Button**:
    *   `data-molsysviewer-addon-back-button="true"`

### B. Behavior on Structure Rebuild / Reload
*   When a new structure is loaded or regenerated (which triggers a `setStructure` call):
    *   The **Navigate** panel will reset its active tab back to **`structure`** (the default view showing the chain sequence strips).
    *   The **Add-ons** panel will retain the active Add-on if one is selected, but will reset the active panel section to the first section in the list, ensuring that any stale widgets are unmounted and freshly reinitialized on the new structure.

