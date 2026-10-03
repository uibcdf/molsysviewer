---
summary: Partial coordinate updates leave interaction analyses and geometry stale
issue: uibcdf/molsysviewer#118
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: high
verification: reproduced
area: [coordinates, interactions, trajectory]
guard: tests/test_coordinate_edits.py
normative:
blocked_by: []
supersedes: []
---

# Partial coordinate updates leave interaction analyses and geometry stale

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

The final pre-1.0 design review reproduced a public coordinate-edit path that changes `view.molsys` without reconciling derived scientific or visual state. Moving an acceptor by 1 nm with `view.partial_coordinates_update(...)` left the projected interaction endpoint unchanged and the edited structure declared evaluated.

Minimal reproduction on a real demo with controlled synthetic observations (requires the experimental MolSysMT Interactions provider used for #114):

```python
import numpy as np
import molsysmt as msm
import molsysviewer as msv
from molsysviewer import pyunitwizard as puw

view = msv.new_view(msv.demo["pentalanine"].molsys, structure_indices=[0, 8, 3])
r = msm.Interactions.from_records(
    [{"structure_index": 0, "interaction_type": "hbond", "participants": [
        {"role": role, "atom_indices": [i]}
        for i, role in enumerate(("donor", "hydrogen", "acceptor"))
    ]}], n_atoms=view.molsys.get_n_atoms(), n_structures=3,
    evaluated_structure_indices=[0], method="review_fixture",
)
view.interactions.attach(r, name="contacts", assume_aligned=True)
view.interactions.add("contacts", tag="hb")
xyz = puw.get_value(msm.get(view.molsys, coordinates=True, structure_indices=[0]), to_unit="nm")
view.partial_coordinates_update(
    puw.quantity(xyz[:, 2:3, :] + np.array([[[1.0, 0.0, 0.0]]]), "nm"),
    selection=[2], structure_indices=0,
)
```

## How

`molsysviewer/viewer/scene.py:partial_coordinates_update` mutates native coordinates and sends an in-place frontend update without invoking the interaction revision/invalidation mechanism. The message also omits the target structure indices and reduces a multi-structure array to its first structure. The TS handler edits the currently loaded structure. The stale scientific coverage and Python projection were reproduced; the frame-addressing discrepancy was inspected in source, not certified through browser rendering.

## Why

Scientific measurements and graphics can silently describe coordinates that are no longer the current system. This contradicts the edit-reconciliation contract. This is a viewer-owned integration defect, not a claim that the MolSysMT detector is wrong.

## Acceptance

Public coordinate edits must identify affected structures, invalidate geometry-dependent scientific coverage, advance revisions and reconcile cached/anchored visual state. A non-visible or nonconsecutive structure edit must not be applied to the wrong visible frame. Invalid requests must leave the system unchanged. Guards must use real demos and assert coverage, endpoints and real-browser frame behavior.

This is pre-1.0 integrity work associated with #114.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

Coordinate edits validate their complete atom/frame batch before mutation, invalidate named scientific interaction coverage only on edited structures, clear dependent caches/history and refresh the lazy molecular projection. An active native transfer is superseded so old buffers cannot overwrite the edit. Partial transport carries explicit frame indices, a 3-D coordinate array and Å units; new Mol* model/conformation identities rebuild geometry.

The guard asserts nonconsecutive frame writes, unchanged other frames/atoms, invalidated evaluated coverage, absence of stale links, current exported coordinates and cancellation of old native transfers. Removing the finite-coordinate check makes its rejection guard fail. The real Mol* coordinate-edits browser suite also passes for offscreen structures and preserves the untouched frame.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
