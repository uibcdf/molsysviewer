# TopoMT-Requested Generic Visualization Primitives

**Status:** pending
**Requester:** TopoMT / `molsysviewer_topomt`
**Owner:** MolSysViewer

## Ownership Principle

Reusable geometry, styling, and interaction primitives that any molecular
system or addon could use belong in MolSysViewer. Logic that derives geometry or
scalars from DFND semantics remains in `molsysviewer_topomt`.

## Requested Primitives

- **Ring and stacked-ring shape:** circles perpendicular to a path axis, with
  radius and color per station, for pore profiles and bottleneck accents.
- **Focus-with-fade:** dim molecular representations outside a selected region to
  expose buried features.
- **Clipping-plane primitive:** programmatic section plane through a point and
  normal.
- **Per-vertex surface scalar coloring:** project curvature, electrostatics,
  conservation, or another scalar onto a molecular surface.
- **Legend overlay and CVD-safe palette catalog:** reusable legends and
  color-blind-safe palettes for addons.
- **Synchronized 2D-3D trajectory plot:** click or hover a scalar time series to
  set the corresponding molecular frame and display events.

## TopoMT Use Cases

These primitives support DFND channel profiles, buried void inspection,
convexity and property heatmaps, multi-component legends, and dynamic pocket
analysis. TopoMT would supply entity references, geometry, and scalar values;
MolSysViewer would own generic rendering and interaction behavior.

## Validation Expectations

Each accepted primitive should have a viewer-level public contract, repeated
render/update/clear tests, standalone behavior where applicable, and examples
that do not depend on TopoMT.
