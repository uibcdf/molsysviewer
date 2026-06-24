# Generic Geometry Payloads and Structured Shape Entity References

Status: pending proposal from TopoMT WP-18
Date: 2026-06-15

## Problem

Viewer addons independently define geometry transport objects, attach units, call shape methods with `skip_digestion=True`, and recover scientific identity from shape interactions. MolSysViewer currently exposes shape tags, labels, and selected atoms, but not arbitrary structured entity references. This forces addons either to maintain side registries or to reconstruct identity from atoms.

## Proposed Host Contract

1. Provide generic, viewer-neutral immutable payloads for points, segments, indexed triangles, indexed tetrahedra, and spheres. Coordinates and identity references must be separate fields, and units must be mandatory.
2. Provide final-boundary shape adapters that accept those payloads, attach/convert PyUnitWizard quantities, and bypass redundant digestion internally.
3. Allow shape/group source data to carry JSON-serializable `entity_refs`, and include the picked group reference in hover, click, context-menu, and active-selection events.
4. Preserve explicit atom-index-space metadata for indexed primitives. The host should not infer an index space from values.

## Ownership Boundary

MolSysViewer owns generic geometry transport, shape adapters, and interaction transport. Domain addons own scientific extraction and references: for example, TopoMT owns DFND face permeability, tetrahedron/component identity, and selection through DFND selectors.

## Evidence from TopoMT WP-18

TopoMT currently has local provisional `PointGeometry`, `SphereGeometry`, `SegmentGeometry`, `TetrahedraGeometry`, `IndexedTriangleGeometry`, `IndexedEdgeGeometry`, final adapters, and structured `EntityRef`. They prove cross-renderer equivalence, mandatory units, and stable structured identity. The diagnostic action no longer parses hover labels, but direct host transport of `entity_refs` would remove the remaining reconstruction/registry requirement.

## Additional Host Evidence

- `add_sphere` currently overloads scalar and collection inputs: a one-row center matrix changes tag generation and requires per-item colors, while a single center vector preserves the requested tag and requires a scalar color. A generic adapter needs an explicit scalar/collection contract rather than shape inference.
- TopoMT adapters pass `skip_digestion=True`, but MolSysViewer/ArgDigest still emits `DigestNotDigestedWarning` for many shape kwargs during the addon suite. The host boundary should guarantee that the bypass applies before all nested digesters.

## Acceptance Criteria

- Two addons can use the same generic payload/adapters without importing domain code.
- A picked face/edge/tetrahedron emits its structured `entity_ref` unchanged.
- Units and atom-index spaces are explicit and validated.
- Existing shape APIs remain compatible.
