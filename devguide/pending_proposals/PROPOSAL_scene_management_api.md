# PROPOSAL: Dedicated Scene Management API (`view.scene`)

## Problem Statement
Currently, most scene-level visual properties (background color, fog, lighting, spin, swing) are only accessible via the viewer's graphical user interface (buttons) or are hardcoded into export presets. There is no public Python API to programmatically control the environment, which prevents:
1. Scripting high-quality visual transitions.
2. Synchronizing the environment with analysis results.
3. Creating reproducible visual states for notebook sharing.

## Proposed Solution
Implement a `SceneManager` accessible via `view.scene` that exposes standard Mol* environment operations.

### Proposed Methods

#### 1. Background Control
```python
view.scene.set_background(color='white'|'dark'|'transparent'|hex_int)
```
**Logic:** Sends `toggle_background` or a new `set_background_color` op to the frontend.

#### 2. Fog and Depth
```python
view.scene.set_fog(enabled=True|False)
```
**Logic:** Sends `set_fog` op to Mol*.

#### 3. Lighting and Rendering
```python
view.scene.set_lighting(preset='illustrative'|'flat'|'occlusion', intensity=float)
```
**Logic:** Controls Mol* lighting parameters.

#### 4. Dynamic Effects
```python
view.scene.spin(enabled=True|False, speed=float)
view.scene.swing(enabled=True|False, speed=float)
```
**Logic:** Toggles the automatic rotation or oscillation of the camera.

## Benefits
- **Full Automation:** Users can set up the perfect scene for a figure or a movie entirely from code.
- **API Symmetry:** Brings scene control to the same level of maturity as regions, shapes, and measurements.
- **Consistency:** Ensures that what the user sees in the notebook is what they get in the HTML export (WYSIWYG).

## Implementation Path
- Create `molsysviewer/scene.py` with the `SceneManager` class.
- Link `view.scene` in `MolSysView.__init__`.
- Update `viewer.js` to ensure all these operations are exposed as message handlers.
- Ensure the scene state is recorded in `_message_history` for replayability.
