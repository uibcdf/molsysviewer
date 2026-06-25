# Shape Visibility and Layer Group API

Status: pending
Owner: unassigned
Created: 2026-06-25
Last reviewed: 2026-06-25

## Problem

MolSysViewer exposes a clear public visibility model for molecular regions through
`Region.show()`, `Region.hide()`, `Region.show_only()`, and `Region.delete()`. Addon
shape renderers, however, still rely mostly on shape tags and ad-hoc registries when
users need to compare, hide, show, replace, or delete visual overlays.

TopoMT hit this directly while validating DFND feature representations: repeated calls
with different feature styles can intentionally or accidentally accumulate shape layers
unless the addon maintains its own grouping registry and clears tags manually. This is
manageable, but it puts generic scene-state concerns in each addon instead of the host.

## Requested Host Capability

Provide a stable public API for non-structural visual groups equivalent in spirit to
region visibility:

- create or retrieve a logical layer/group by tag;
- hide/show/delete a group and all member shapes;
- list groups and their member shape tags;
- optionally show only one group within a namespace;
- preserve compatibility with existing shape tags and `layer_tag`.

The API should work for shape-based overlays such as blobs, tubes, rings, triangle
faces, labels, links, scalar surfaces, and addon-generated diagnostics.

## Why This Belongs in MolSysViewer

The underlying operations are viewer-generic: visibility, deletion, grouping, and
scene bookkeeping. Domain addons should decide *what* to render, not reimplement how
shape groups are managed. A host-level API would benefit TopoMT, pharmacophore maps,
network overlays, trajectory annotations, measurement layers, and future addons.

## TopoMT Evidence

`molsysviewer_topomt.show_features()` needs user-facing behavior such as:

- replace the previous feature representation by default;
- allow additive comparison when explicitly requested;
- hide/show/delete a feature-render group without rebuilding the topography;
- keep notebook scenes from becoming visually polluted by stale overlays.

TopoMT can implement a local stopgap through `RenderResult` and tags, but a first-class
host API would make this consistent and discoverable.

## Acceptance Criteria

- A shape group can be hidden and shown without deleting/recreating its shapes.
- A shape group can be deleted by one stable public call.
- The API is usable by addons without accessing private viewer attributes.
- Existing direct shape APIs remain compatible.
- The group model is reflected in the frontend so users can inspect/manage overlays.

## Decision Questions

1. Should this be exposed as a `view.layers` manager, a `view.shapes.groups` manager,
   or a unified scene-object manager?
2. Should groups be purely tag-prefix based or explicit objects created by the host?
3. Should visibility state be queryable from Python after frontend-side changes?
