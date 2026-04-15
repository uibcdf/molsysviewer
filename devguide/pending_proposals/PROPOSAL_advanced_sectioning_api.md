# PROPOSAL: Advanced Sectioning — Pending parts (3 & 4)

## What is already implemented (parts 1 & 2)

- `view.scene.add_section(point, normal, *, invert, tag)` — adds a world-space
  clipping plane to all structural representations.  Returns a `Section` handle.
- `view.scene.remove_section(tag)` / `view.scene.clear_sections()`
- `Section` class in `layers.py`:
  - `get_point()` / `get_normal()` / `is_inverted()`
  - `set_point(point)` / `set_normal(normal)` / `set_invert(invert)` / `delete()`
- TS: `set_sections` op → `setSections` in `scene-handlers.ts`.
  - Converts Python `point` (nm) → Mol* position (Å).
  - Converts `normal` vector → Mol* `{axis, angle(deg)}` rotation from default
    plane normal [0, 1, 0].
  - Applies via `plugin.managers.structure.component.setOptions({ clipObjects })`.

## Pending parts

### Part 3: Interactive canvas gizmos

When a section is active, show a 3D disc/arrow gizmo in the canvas that the
user can grab with the mouse to:
- Translate the plane along its normal.
- Rotate the normal.

The `point` and `normal` attributes in Python should update in real-time as
the user drags.  This requires a bidirectional canvas → Python message channel
for continuous position sync.

### Part 4: Topological integration (mouth references)

```python
view.scene.add_section(
    point="centroid:channel_tag",
    normal="mouth:mouth_tag",   # auto-align to channel entrance
)
```

Auto-computes normal from object centroid → mouth centroid.  Requires TopoMT
integration (how mouth/channel objects expose their spatial data to Python).
