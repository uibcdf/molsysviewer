(User_Overlays_Shapes_Meshes)=
# Mesh primitives

Mesh primitives render custom geometry directly:

- `add_triangle_faces` — arbitrary triangulated surfaces
- `add_tetrahedra` — solid tetrahedra rendered as four triangular faces

Typical uses: convex hulls, binding-site polyhedra, alpha-shape envelopes,
or any geometry computed outside MolSysViewer.

---

## Triangle faces

### Minimal example — explicit vertices

```python
import molsysviewer as mv

view = mv.demo["tctim"]
view

# Each triangle: [[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]] in Å
triangles = [
    [[0, 0, 0], [5, 0, 0], [2.5, 5, 0]],
    [[0, 0, 0], [2.5, 5, 0], [0, 5, 3]],
    [[5, 0, 0], [2.5, 5, 0], [5, 5, 3]],
]

view.shapes.add_triangle_faces(
    vertices=triangles,
    colors=0x88ccff,
    alpha=0.5,
    tag="hull",
)
```

### From atom triplets

```python
# Each triplet is three atom indices; coordinates resolved from the current structure
view.shapes.add_triangle_faces(
    atom_triplets=[[0, 10, 20], [10, 20, 30]],
    colors=[0xff4444, 0x4444ff],
    tag="atom-triangles",
)
```

### Key options

| Parameter | Default | Description |
|---|---|---|
| `vertices` | `None` | List of triangles `[[p1],[p2],[p3]]` in Å. |
| `atom_triplets` | `None` | List of `[i,j,k]` atom-index triplets. |
| `structure_vertices` | `None` | Per-structure vertex lists for trajectory-aware meshes. |
| `colors` | `0xCCCCCC` | Hex color (scalar or one per triangle). |
| `alpha` | `1.0` | Transparency (0–1). |
| `labels` | `None` | Per-triangle labels. |
| `draw_edges` | `None` | Draw triangle edges as thin cylinders. |
| `edge_radius` | `None` | Edge cylinder radius (Å). |
| `edge_color` | `None` | Edge color override. |
| `show_normals` | `None` | Draw face normals as arrows. |
| `tag` | auto | Tag for selective clear/hide. |
| `layer_tag` | `None` | Group tag. |

---

## Tetrahedra

### Minimal example — explicit coordinates

```python
# Each tetrahedron: four vertices [[x,y,z], ...]
tetras = [
    [[0,0,0], [5,0,0], [2.5,5,0], [2.5,2.5,5]],
    [[5,0,0], [10,0,0], [7.5,5,0], [7.5,2.5,5]],
]

view.shapes.add_tetrahedra(
    tetra_coords=tetras,
    colors=[0xff8800, 0x00aaff],
    alphas=0.5,
    tag="alpha-tetras",
)
```

### From atom quads

```python
# Each quad is four atom indices; coordinates resolved from the current structure
view.shapes.add_tetrahedra(
    atom_quads=[[0, 10, 20, 30], [40, 50, 60, 70]],
    colors=0xffcc00,
    exterior_only=True,
    tag="atom-tetras",
)
```

### Key options

| Parameter | Default | Description |
|---|---|---|
| `tetra_coords` | `None` | List of 4-vertex arrays in Å. |
| `atom_quads` | `None` | List of `[i,j,k,l]` atom-index quads. |
| `colors` | `0xFF8800` | Hex color (scalar or one per tetrahedron). |
| `alphas` | `0.6` | Transparency (scalar or one per tetrahedron). |
| `exterior_only` | `True` | Render only the three exposed faces (hide base). |
| `show_all_faces` | `None` | Show all four faces regardless of `exterior_only`. |
| `draw_edges` | `None` | Draw edges as cylinders. |
| `show_normals` | `None` | Draw face normals as arrows. |
| `tag` | auto | Tag for selective clear/hide. |
| `layer_tag` | `None` | Group tag. |

---

## Clearing

```python
view.shapes.clear(tag="hull")
view.shapes.clear()
```
