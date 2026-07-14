# Studio subpanel — Shapes (spec)

**Status:** implemented (2026-07-14). This spec and the
[UI design](studio_shapes_subpanel_ui_design.md) describe the live panel.
References to "today" below describe the audited pre-implementation baseline.

**Normative:** [`scene_contracts.md`](../scene_contracts.md). This spec
points at the contracts; it does not restate them.

---

## 1. What this panel is for

Shapes are the **overlay geometry**: the sphere that marks a site, the tube through a
channel, the vectors of a mode, the pocket surface. They are what turns a structure
into a figure.

Today the panel lists them as anonymous rows and lets you focus, hide and delete.
**Every single style knob is unreachable** — colour, alpha, radius, scales — although
the `Shape` object has had them all along. And when a shape **fails to render**, the
panel says nothing.

## 2. The domain, and its two structural problems

### 2.1 The manager is the poorest of the five

`ShapesManager` lacks **`count`, `records`, `delete`, `set_tag`, `show`, `hide`** —
all six of which annotations and measurements have. To hide a shape you must drop to
the object (`view.shapes['tag'].hide()`), while the others offer
`view.annotations.hide(tag)`.

**This is very likely why the Shapes panel bypassed Python and called
`handleMessage` directly** (§0.2): the API did not offer it the same moves. The
architectural defect and the API gap are the same wound. **Phase 0 (Contract S0)
closes it**, and this panel is built on the result.

### 2.2 The mutators are *not* uniform across shape types

**This is the trap of this panel.** The style methods on `Shape` each check the
shape's wire `op` and raise `NotImplementedError` otherwise. A panel offering generic
controls will show buttons that blow up.

The real matrix (verified 2026-07-12 against `molsysviewer/layers.py`):

| shape (wire `op`) | `set_color` | `set_colors` | `set_alpha` | `set_radius` | `set_radii` | `set_radius_scale` | `set_length_scale` | `set_center` | `set_coordinates` |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `add_sphere` | ✅ | — | ✅ | ✅ | — | — | — | ✅ | ✅ |
| `add_network_links` | — | ✅ | ✅ | — | ✅ | — | — | — | ✅ |
| `add_channel_tube` | — | ✅ | ✅ | — | ✅ | — | — | — | ✅ |
| `add_tetrahedra` | — | ✅ | ✅ | — | — | — | — | — | ✅ |
| `add_triangle_faces` | — | ✅ | ✅ | — | — | — | — | — | ✅ |
| `add_anisotropy_ellipsoids` | — | ✅ | ✅ | — | — | — | — | — | ✅ |
| `add_pharmacophore_features` | — | ✅ | ✅ | — | ✅ | — | — | — | ✅ |
| `add_displacement_vectors` | — | — | — | — | — | ✅ | ✅ | — | ✅ |
| `add_pocket_blob` | — | — | ✅ | — | ✅ | ✅ | — | — | ✅ |
| `add_pocket_surface` | — | — | ✅ | — | — | — | — | — | ✅ |
| `add_alpha_sphere_set` | — | — | — | — | — | — | — | — | ✅ |
| **`add_hbonds`** | — | — | — | — | — | — | — | — | — |
| **`add_rings`** | — | — | — | — | — | — | — | — | — |
| **`add_scalar_isosurface`** | — | — | — | — | — | — | — | — | — |

**The matrix is keyed on the wire `op`, and the API has more names than there are
ops.** Three traps for anyone building the panel from the API surface instead:

- `add_gaussian_isosurface` **is `add_scalar_isosurface`** — a literal alias
  (`pocket_blobs.py:142`), same op. It is removed in Phase 0; do not give it a row.
- `add_interaction_sites` emits `add_pharmacophore_features` — so it **does** support
  that row's mutators.
- `add_topomt_feature` is a **dispatcher**: it delegates to `add_pocket_surface` and
  `add_channel_tube`. It is not a shape type and has no op of its own.

Three things this table says out loud:

- **`set_color` (singular) works only on spheres.** Everything else colours through
  `set_colors` (plural, per element). A single "Colour" button that calls `set_color`
  breaks on 13 of 15 types.
- **Four types support nothing at all** — `add_hbonds`, `add_rings` and the two
  isosurfaces emit wire ops that no mutator recognises. Not even `set_alpha`.
- `focus()` and `get_coordinates()` are the only near-universal operations.

**The panel must derive its controls from the shape's kind, from this matrix.** It
must never present a control that will raise.

## 3. What the domain does offer

- **`info(tag=None)`** → `kind`, `tag`, `layer_tag`, `color` (hex), `radius`/`width`,
  `center(s)`, `visible` — already a panel-ready summary.
- **`render_status(tag=None)`** → runtime diagnostics for trajectory-bound shapes:
  whether the shape resolved on the current frame. **Runtime-only by design** (its
  docstring: not part of the reproducible scene history) — a **diagnostic, not scene
  state** (§4).
- On `Shape`: the matrix above, plus `focus()`, `get_center()`, `get_coordinates()`.

## 4. Scope

**In:**

- Per-shape **style controls, derived from the kind** (the matrix).
- **Render diagnostics**: a ⚠ on the row when a shape does not resolve on this
  frame, with the cause in a tooltip (*"invalid coordinates at frame 42"*). A Shapes
  panel that stays silent when a shape fails to draw is hiding the one thing the user
  needs.
- Lifecycle: rename, layer, show/hide, delete, clear — **through the new manager
  methods from Phase 0**, not by reaching into the object.

**Out:**

- **Creating shapes from the GUI.** The 15 constructors take geometry (centres,
  vertices, coordinate pairs) that has no sane GUI. Shapes are created from Python or
  by an addon. The panel **manages** them.
- **Custom-shape authoring** (Bloque 4): stays deferred.
- Fixing the four types that support no mutators: out of this slice. The panel simply
  shows no style controls for them (and that honesty is the feature).

## 5. What "done" means

- The style controls shown on a row are exactly those its kind supports. **No control
  in this panel can raise `NotImplementedError`.**
- A shape that fails to render says so, with the reason.
- Every affordance goes through Python (Contract S2) — the eye no longer repaints
  Mol\* behind Python's back.
- Shapes **survive a save/reload** (Contract S5 — today `export_state` has no
  `shapes` key at all, §0.3) and deleting one is **undoable** (S6).
