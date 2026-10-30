# Receiving independent chemical domains

**Role:** operational source-receiving guide for
[uibcdf/molsysviewer#269](https://github.com/uibcdf/molsysviewer/issues/269),
coordinated with `uibcdf/molsysmt#255` and `uibcdf/molsyssuite#155`.
This guide does not establish a new published dependency minimum or installed
artifact qualification.

## Projecting a molecular system

Topology supplies stable inventory. Read covalent bonds through
`molsys.chemical_states.get_bonds(chemical_state="reference")`, not through a
Topology facade. JSON and array-native serialization use the same static
projection. A declared nonzero reference is honored. An ambiguous reference
raises; no arbitrary state is selected. Missing chemistry, a zero-state
collection, unknown connectivity and complete empty connectivity remain
unchanged in the native system. No edges are inferred to make rendering succeed.
The static payload has no per-structure state-switching protocol.

Active selection queries only available hierarchy metadata and excludes missing
memberships from its per-level index lists. It retains the ordered atom
selection. A collection without chemical states does not provide component
metadata. Group and chain rendering fallbacks are not native assignments.

## Declaring composition and edits

Provide `[topology, chemical_states, structures]` when an operation needs all
three domains. `[topology, structures]` projects inventory and geometry without
recovering chemistry from a hidden owner. Appending independent molecular
systems currently needs the provider's supported state-alignment policy; do not
invent an unknown state in Viewer to bypass a rejected composition.

Use supported molecular extraction/removal to remap structures, chemical-state
associations and named analyses together. Replacing only Structures can leave
explicit associations or analyses on the previous axis and is correctly rejected.
When a workflow intentionally changes labels and then appends only coordinates,
pass the Structures source explicitly; do not request a merge of differently
labeled full molecular inventories.

Positive chain-composition fixtures declare their chain membership. The bundled
legacy pentalanine file stores unassigned atom-to-chain positions; those are not
silently repaired. Separate tests retain unknown and partial membership coverage.

## Executable receiving boundaries

- `tests/loaders/test_array_native_molsys.py` checks reference-state access,
  ambiguity, missing/empty chemistry, coordinate values/units and unchanged storage.
- `tests/test_active_selection.py` checks unknown and partial membership,
  unavailable domains and unchanged ordered atom selection.
- `tests/test_composite_load.py`, `tests/test_live_edit_rebuild.py`,
  `tests/test_managed_axis_growth.py` and
  `tests/test_structure_edit_correspondence.py` check composition, coherent
  scientific edits and retained scene/source maps.
- The provider's `tests/molsysviewer_molsysmt/` guards cover the scientific add-on,
  including scene-failure retries without repeating completed molecular edits.

Run the ordinary Python source lane:

```bash
python -m pytest --receptor=llm -m "not qt_runtime" tests
```

Experimental real Qt windows retain their separate lane.
For Chrome export tests, use a managed short temporary directory: Unix-domain
socket paths have a bounded length. Keep large pytest outputs on repository disk;
do not substitute skipped browser tests for actual rendering evidence.

Record exact provider/consumer sources and retained worktree changes. Source
compatibility, the independently versioned provider package floor, browser
qualification and installed/release gates remain different claims. The dated
Studio operation inventory retains its inspected historical symbols; current
scientific graph tools belong to `molsysmt.chemical_states`, while sequence tools
remain under `molsysmt.topology`. Quarantined historical code is not a current
receiving route.
