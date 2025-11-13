# TopoMT — Feature Attributes Catalog

This document defines **purely geometric, energy-agnostic attributes** for each **feature dimensionality class (0D / 1D / 2D)** in the TopoMT topographic model.  
These attributes are intended to be the **core structural descriptors** used for indexing, ranking, graph construction, and machine learning applications.


## 0D Features — (points)

| Attribute                | Type / Unit                        | Description                                                                                         | Notes |
|---------------------------|-------------------------------------|-----------------------------------------------------------------------------------------------------|-------|
| `point_type`              | Enum                               | Category of the point (`pit`, `apex`, `bifurcation`, `saddle_point`, `nadir`, `ridge_tip`, …)        | Must match the feature catalog. |
| `coordinates`             | 3D vector (Å)                       | Cartesian coordinates of the point.                                                                 | Required for all points. |
| `curvature_context`       | float                              | Local curvature or shape index at the point (optional).                                              | Useful for apex/pit prominence. |
| `morse_index`             | int                                | Morse index of the point (0,1,2) if critical point analysis is used.                                 | Optional advanced descriptor. |
| `parent_ids`              | list[str]                          | IDs of associated 2D parents.                                                                        | Typically 1; can be >1 for branching points. |
| `adjacent_boundaries`     | list[str]                          | Boundary features attached to this point.                                                            | Useful for connectivity graphs. |
| `depth_or_height`         | float (Å)                           | Signed distance from a reference surface (e.g., cavity floor or convex hull).                        | Pit negative, Apex positive. |
| `prominence`              | float                               | Relative geometric prominence (e.g., apex height or pit depth normalized by neighborhood radius).    | Purely geometric measure. |

---

## 1D Features — (boundaries)

| Attribute                | Type / Unit                        | Description                                                                                             | Notes |
|---------------------------|-------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| `boundary_type`           | Enum                               | Type of boundary (`mouth`, `baserim`, `neck`, `ridge`, `furrow`, `seam`, `isthmus`, `branchline`, …).    | Must match the feature catalog. |
| `parent_ids`             | list[str]                           | IDs of associated 2D parents.                                                                            | Typically 1, but 2 for seams/bridges. |
| `point_ids`              | list[str]                           | IDs of 0D points (endpoints, bifurcations, ridge tips, etc.).                                            | Optional. |
| `length`                  | float (Å)                           | Total curve length.                                                                                      | Required. |
| `curvature_profile`       | float / list[float]                 | Mean curvature or full curvature along the curve.                                                        | Optional. |
| `torsion_profile`         | float / list[float]                 | Mean torsion or torsion series along the curve.                                                          | Optional. |
| `is_closed`               | bool                               | Indicates whether the boundary is a closed loop (e.g., mouth loop).                                      | Useful for loops and topological genus. |
| `branch_degree`           | int                                | Number of bifurcations connected to this curve.                                                          | ≥0 |
| `orientation_vector`      | 3D vector                           | Representative direction (e.g., principal axis).                                                         | Optional for axis-aligned boundaries. |
| `adjacent_surfaces`       | list[str]                           | IDs of neighboring 2D features along the curve.                                                          | Essential for connectivity graphs. |
| `geodesic_position`       | float or list[float]                | Normalized position(s) along parent surfaces.                                                            | Useful for mapping pharmacophore positions. |
| `shape_metrics`           | dict                                | Elongation, sinuosity, curvature statistics.                                                             | Optional advanced descriptors. |

---

## 2D Features — (shape surfaces)

| Attribute                  | Type / Unit                       | Description                                                                                                            | Notes |
|----------------------------|------------------------------------|--------------------------------------------------------------------------------------------------------------------------|-------|
| `shape_type`               | Enum (`concavity`, `convexity`, `mixed`) | Type of surface feature.                                                                                         | Mandatory. |
| `feature_type`             | Enum                              | Specific subtype (e.g., `pocket`, `channel`, `protrusion`, `interface`, etc.).                                        | Mandatory. |
| `boundary_ids`            | list[str]                          | Associated 1D boundary features.                                                                                       | Links to boundaries. |
| `point_ids`               | list[str]                          | Associated 0D point features.                                                                                           | Links to critical points. |
| `surface_area`            | float (Å²)                          | Total surface area of the patch.                                                                                        | Required. |
| `perimeter`               | float (Å)                           | Total perimeter length of boundary loops.                                                                              | Required for closed patches. |
| `mean_curvature`          | float                               | Average mean curvature.                                                                                                | Useful for protrusion/concavity strength. |
| `gaussian_curvature`      | float                               | Average Gaussian curvature.                                                                                            | Useful for classification. |
| `openness_angle`          | float (radians or degrees)          | Solid angle of opening (for pockets/funnels).                                                                         | Geometric gating descriptor. |
| `sphericity`              | float                               | 0–1 measure of roundness.                                                                                              | Optional. |
| `elongation`              | float                               | Ratio of longest to shortest axis.                                                                                    | Optional. |
| `accessibility_index`     | float                               | Purely geometric accessibility metric.                                                                                | Energy-agnostic accessibility. |
| `principal_axes`          | 3x3 matrix / 3 vectors               | Principal orientation axes.                                                                                            | Optional but useful for alignment. |
| `centroid`                | 3D vector                           | Geometric center of the patch.                                                                                        | Required for many calculations. |
| `connectivity_degree`     | int                                 | Number of neighboring 2D patches.                                                                                     | Useful in interface networks. |
| `genus_or_holes`          | int                                 | Topological genus or number of holes in the surface.                                                                   | Optional advanced descriptor. |
| `hierarchy_level`         | int                                 | Depth in topographic hierarchy (e.g., channel branch depth).                                                           | Optional for traversal. |

