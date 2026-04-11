# PROPOSAL: Programmatic control for Trajectories and Structures

## Problem Statement
The current Python API lacks methods to control the viewer's timeline. While Mol* provides a slider and playback controls in the UI, users cannot programmatically jump to a specific frame or structure from a Python script or notebook cell. This limits the ability to create scripted animations, "movies", or to synchronize the view with external analysis.

## Proposed Changes

### 1. Programmatic Structure Control
Since MolSysMT systems use structure indices or IDs, the viewer should support navigating through them programmatically:
```python
view.set_structure(index: int)
view.set_structure_id(id: str)
```
**Logic:**
- `set_structure(index)`: Sends the `set_trajectory_frame` operation to the frontend with the provided structure index.
- `set_structure_id(id)`: Queries `_molsys` to find the index of the structure with the given ID, then jumps to that position in the timeline.

### 2. State Querying
Add a public property to retrieve the current state:
```python
view.current_structure_index  # Returns the index of the structure being displayed.
view.current_structure_id     # Returns the ID of the structure being displayed.
```

### 3. Playback API
Add basic playback controls:
```python
view.play()
view.pause()
view.set_play_speed(speed: float)
```

### 3. Removal by Structure ID
Extend the `view.remove()` method to support structure IDs:
```python
view.remove(structure_id='tag')
```
**Logic:** Resolves the ID to an index before performing the removal from the molecular system and re-rendering the view.


## Benefits
- **Reproducibility:** Allows a notebook to automatically set the viewer to a specific state of interest (e.g., "Jump to the frame where the ligand binds").
- **Scripting:** Enables the creation of complex visual sequences.
- **Semantic Navigation:** Easier for users to reason about "Structure ID 'equilibrium'" rather than "Frame 452".

## Implementation Path
- Implement the mapping logic in `MolSysView` using `msm.get(self._molsys, element='structure', ...)` to resolve IDs to indices.
- Update `viewer.js` to handle speed updates if not already exposed.
- Add these methods to the `whole` object as well for consistency: `view.whole.set_frame()`.
