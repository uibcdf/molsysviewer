---
summary: View copy and extraction lose scene objects, interaction sets and region colors
issue: uibcdf/molsysviewer#119
status: resolved
opened: 2026-09-30
closed: 2026-09-30
severity: high
verification: reproduced
area: [scene, extraction, copy]
guard: tests/test_scene_transfer.py
normative:
blocked_by: []
supersedes: []
---

# View copy and extraction lose scene objects, interaction sets and region colors

**Reported:** 2026-09-30, final pre-1.0 design review using real demos.

## What

The final design review reproduced loss of scene state through public view transformations:

```python
import molsysviewer as msv
view = msv.new_view(msv.demo["dialanine"].molsys)
view.shapes.add_sphere(tag="s")
view.annotations.add(text="label", atom_indices=[0], tag="a")
view.regions.add(atom_indices=[0, 1, 2], tag="A").set_color(0x112233)
c = msv.tools.basic.copy(view)
e = view.extract(selection="all")
print(c.shapes.records(), c.shapes.tags(), c.export_state()["shapes"])
print(e.export_state()["regions"][0]["color_layer"])
```

The copy retains replay records but exposes no shape/annotation objects through their managers; its exported shape list is empty. Copy and extraction lose region-owned color layers. With a named scientific analysis and a tagged Interactions display from #114, both transformations preserve the analysis but lose the visual display. The extraction case also used nonconsecutive structure indices `[2, 0]`.

## How

`tools/basic/copy.py` delegates scene migration to `tools/basic/merge.py:_import_view_state`, which migrates selected replay messages without consistently recreating canonical objects. `tools/basic/extract.py:_import_extracted_state` has its own hand-maintained field/domain list. Region recreation flattens recipes into atom lists and omits owned colors and other state; neither route migrates the new interaction sets.

## Why

A new view must remain queryable, editable, saveable and replayable with coherent registries. An apparent copy must not silently lose scientific presentation. MolSysMT remaps the scientific analyses; MolSysViewer owns preserving/remapping their visual references.

## Acceptance

Share scene preservation/remapping mechanisms where possible. Preserve eligible objects, recipes, dependencies, ordering, colors, layers, owner/visibility and interaction references across copy/extraction and the related merge path. Remap atom and structure axes explicitly, preserve broken references where the contract requires them, and retain existing extraction semantics for absent anchors. Assert both records and retrievable objects, state/session/reconstruction fidelity and independent mutation of the new view.

## What was refuted

The review preserved the existing working tree. These findings concern public scene contracts, not an upstream chemical detector error. No browser outcome was inferred from a sent message.

## Resolution

Copy, extraction and merge now share canonical scene-state transfer. Atom/frame maps preserve colors, typed handles, annotation options, measurement anchors, saved selections and interaction filters. Extraction also remaps focus styling. Index-specific region recipes freeze with their original recipe retained when the index space changes. Incomplete interaction filters remain broken. Merge rejects inputs with named scientific analyses until an explicit scientific merge contract can preserve them.

The guard checks canonical copy equality and independent mutation, remapped nonconsecutive frames/atoms, scientific references, colors and retrievable objects, annotation options and focus styling. Removing the incomplete-filter check makes the extraction-broken assertion fail. The merge rejection is an explicit support boundary, not a scientific merge implementation.

Validation on 2026-09-30: targeted regression selections pass; TypeScript checking,
runtime rebuild, JS 293/293 and core browser 36/36 pass. Eight protection mutations
fail and each original file was restored byte for byte. Performance checks pass.
The one full Python run had 2,303 passed, 20 skipped and nine failures; those
failures were corrected and the affected selections pass. The full suite was
not repeated under the repository one-full-run rule. This is not an all-green
exact-candidate gate. Incremental strict Sphinx passes; a clean build retains
six pre-existing MyST heading warnings, with no API import/reference warnings.
