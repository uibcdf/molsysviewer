---
summary: Mixed partial-hierarchy loading accepts a candidate that cannot export scene state.
issue: uibcdf/molsysviewer#157
status: resolved
opened: 2026-10-04
closed: 2026-10-04
severity: high
verification: reproduced
area: [loading, state, history]
guard: tests/test_loading_identity_prevalidation.py
normative: devguide/scene_contracts.md
blocked_by: []
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
## Resolution — 2026-10-04

The detached composition now calls the existing state-identity owner before the
loading owner commits it. Failure raises a descriptive `ValueError` with the
provider exception retained as its cause. The new regression module covers a
malformed native topology and the real protein/caffeine case, including retained
scene objects, sources, analyses, undo/redo and session saving. All five targeted
cases pass in `molsyssuite@uibcdf_3.14`. The malformed native input makes this
guard durable after nullable membership is repaired; the real-input tests then
exercise normal composition, regions/history and session restoration rather
than skipping the case. With the current provider they assert refusal before
active-state mutation, not mixed-source feature availability.

This resolves the Viewer's preparation defect. Direct SDF count dispatch and
partial-hierarchy queries remain open under uibcdf/molsysmt#312/#313; the mixed
scientific support and published-artifact qualification stay in #151. No provider
code or fabricated hierarchy is introduced. Complete source regression evidence
is recorded in the current checkpoint and the scientific review follow-up.

## Correction — 2026-10-04 — provider repair changes the negative fixture

The claim above that the out-of-range group-parent fixture remains a refusal
guard after the provider repair was false. MolSysMT commit `577d0ab32` maps
unmatched parents to missing identities, so that fixture now exports valid scene
state and is accepted. The targeted Viewer test exposed this change before the
full regression. Its negative fixture now uses genuinely ambiguous duplicate
group keys: public identity lookup raises `pandas.errors.InvalidIndexError`,
preserved as the loading refusal's cause. This changes the regression input,
not the product's prevalidation policy. The real protein/caffeine branch continues
to exercise successful composition when the repaired provider is present.
