# Feature Hierarchy in TopoMT

```{admonition} Conceptual overview
:class: tip
The topographic entities in **TopoMT** are organized according to their **geometrical dimensionality** and **shape type**.  
Each *Feature* belongs to one of five canonical geometrical categories:

- `concavity` – inward or hollow regions (e.g., cavities, channels, voids).  
- `convexity` – outward or protruding regions (e.g., bumps, ridges).  
- `mixed` – transitional regions containing both concave and convex components.  
- `boundary` – edges or contours separating regions of different shapes.  
- `point` – zero-dimensional entities, used occasionally as markers or vertices.

Each *Feature* also has a `feature_type` describing its ontological role (e.g., pocket, mouth, ridge) and a unique `feature_id` identifying it within a `Topography` object.
```

---

## Canonical taxonomy

```{note}
The classes `Cavity` and `Vexity` are *canonical generic features*, not specific ones.  
They exist as entry points for unclassified concavities or convexities, and as root nodes of their respective families.
```

### 2D features — Surfaces

| Class | `shape_type` | Description |
|--------|---------------|-------------|
| **Cavity** | `concavity` | Generic concave feature. Base class for `Pocket`, `Channel`, `Void`. |
| **Vexity** | `convexity` | Generic convex feature. Base class for `BaseRim`, `Ridge`. |
| **Interface** | `mixed` | Transitional surface between concave and convex regions. |
| **Boundary** | `boundary` | General border separating topographic regions. |

### 1D features — Edges

| Class | `shape_type` | Description |
|--------|---------------|-------------|
| **Mouth** | `boundary` | Edge delimiting a concavity (e.g., pocket entrance). |
| **BaseRim** | `boundary` | Edge delimiting a convexity. |
| **Neck** | `boundary` | Narrow passage connecting two adjacent features. |
| **Ridge** | `boundary` | Line of maximal convexity, separating convex regions. |

*(In the future, 0D entities such as `Apex` or local critical points may be added.)*

---

## UML diagram

```{uml}
@startuml
skinparam class {
  BackgroundColor White
  BorderColor Black
  ArrowColor Gray
  FontSize 14
}

abstract class Feature {
  +feature_id: str
  +feature_type: str
  +shape_type: Literal["concavity","convexity","mixed","boundary","point"]
  +dimensionality: int
}

' --- 2D Features ---
class Cavity {
  shape_type = "concavity"
}
class Vexity {
  shape_type = "convexity"
}
class Interface {
  shape_type = "mixed"
}
class Boundary {
  shape_type = "boundary"
}

' --- Subtypes of Concavity ---
class Pocket
class Channel
class Void

' --- Subtypes of Convexity ---
class BaseRim
class Ridge

' --- 1D Boundary Features ---
class Mouth
class Neck

' --- Relationships ---
Feature <|-- Cavity
Feature <|-- Vexity
Feature <|-- Interface
Feature <|-- Boundary

Cavity <|-- Pocket
Cavity <|-- Channel
Cavity <|-- Void

Vexity <|-- BaseRim
Vexity <|-- Ridge

Boundary <|-- Mouth
Boundary <|-- Neck
@enduml
```

---

## Integration into the documentation

You can place this file as a standalone page at:
```
docs/content/user_guide/feature_hierarchy.md
```

Then include it in your `toctree` under the *User Guide → Concepts* section.  
Alternatively, embed the UML block and tables in `docs/content/about/what_is_topomt.md` to provide an overview of the library's core entities.

