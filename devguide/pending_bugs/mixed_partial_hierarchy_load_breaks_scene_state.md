---
summary: Mixed partial-hierarchy loading accepts a candidate that cannot export scene state.
issue: uibcdf/molsysviewer#157
status: open
opened: 2026-10-04
closed:
severity: high
verification: reproduced
area: [loading, state, history]
guard:
normative: devguide/scene_contracts.md
blocked_by: [uibcdf/molsysmt#313]
supersedes: []
---

# Mixed partial hierarchy breaks scene state after loading

**Reported:** 2026-10-04, scientific-use review of the integrated source.

## What

Adding a publicly converted caffeine MolSys to a protein scene succeeds, but the
next `view.export_state()` or history-wrapped region operation fails. The active
MolSys has already been replaced by a composition that cannot provide the atom
identity columns needed by the existing scene contract.

```python
from pathlib import Path
import molsysmt as msm
import molsysviewer as msv

data = Path(msm.__file__).resolve().parent / 'data'
view = msv.new_view(str(data / 'pdb/1vii.pdb'), structure_indices=[0])
ligand = msm.convert(str(data / 'sdf/caffeine.sdf'), to_form='molsysmt.MolSys')
view.load(ligand)
view.export_state()  # provider group getter raises IndexError
```

## How

The real review combines 1VII, 1L2Y, 1TCD and 1ATP successfully (7,953 atoms),
then adds converted caffeine. A subsequent `regions.add` starts history capture
through `export_state`, `_structure_identity` and `_read_atom_identities` in
`viewer/state.py`. The provider's group getter indexes a NumPy array with a
nullable membership column. Public provider composition/query alone reproduces
the failure (620 atoms, 36 groups, 24 missing memberships); see
uibcdf/molsysmt#313. Source HEAD is `033c12b3`, with unrelated dirty provider files;
this is experimental source evidence, not a published-artifact result.

`loaders/_composition.py` validates coordinates, frame counts and box/time shapes
on the detached candidate. It does not validate the reusable scene-identity
prerequisites before the loading owner commits that candidate.

## Why

Protein plus small-molecule composition is part of the #151 use case. Partial
hierarchy must remain explicit and usable, and failed preparation must preserve
the prior system, scene, sources, history and analyses. A provider failure must
not leave a successfully loaded but unexportable scene.

## What was refuted

The first four-PDB driver stopped at an assertion comparing the public immutable
region tuple to a list. Correcting that exercise assumption revealed the actual
SDF failures; the tuple/list mismatch is not a product defect.

The direct SDF count route fails separately under uibcdf/molsysmt#312. Converting
SDF publicly avoids that dispatcher, but does **not** provide a complete workbench
workaround: the later mixed-hierarchy group query still fails. Standalone group
absence and a mixed system containing some known groups are different cases.
The Viewer must not invent hierarchy or cast missing memberships to real groups.

## Acceptance and next correction

The provider owns nullable/missing hierarchy through public getters, composition,
extraction and H5MSM. The Viewer loading owner must prevalidate the scene identity
contract using the existing reusable owner before active-system mutation. Guard
refusal and preservation with the real protein/caffeine workflow; with the fixed
provider, guard normal regions/history/state/session use and retained source maps.
The report stays open; no guard or correction is claimed yet.
