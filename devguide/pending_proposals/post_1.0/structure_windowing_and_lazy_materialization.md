# Structure windowing and lazy materialization

**Status:** post-1.0 research and contract design. Not implemented.

MolSysMT speaks about structures and `structure_indices`; a sequence of
structures is not necessarily a trajectory. Playback is a MolSysViewer concern
that may interpret an ordered sequence as a trajectory, but the underlying data
contract must remain general.

## Deferred decision

MolSysViewer 1.0 keeps the current model:

- `view.molsys` is a `molsysmt.MolSys`;
- every selected structure is materialized;
- scientific operations and add-ons see the complete selected system.

The following questions are deliberately deferred because they change that
public meaning:

- eager versus windowed load policy;
- structures resident versus available from a source;
- whether `view.molsys.structures` is complete;
- how direct `msm.get(view.molsys, structure_indices="all")` behaves;
- how add-ons request non-resident structures;
- how edits, append, remove, and topology changes affect a lazy source;
- materialization, eviction, cancellation, and failure semantics.

## Research direction

A future design may separate:

```text
MolSysView
├── resident scientific MolSys
├── form-neutral structure source
├── bounded structural array cache
└── one or more rendering consumers
```

MolSysMT would need a form-neutral API for exact structural blocks as contiguous
arrays, with explicit structure identities, units, dtype, ordering, access
capabilities, and resource lifecycle. The API must not call every ordered
structure sequence a trajectory.

## Questions that must be answered first

1. Is a source-backed `molsysmt.MolSys` desirable, or should source and resident
   `MolSys` remain separate objects?
2. What does public `view.molsys` return when only some structures are resident?
3. Which operations can work from one structure, which need arbitrary
   `structure_indices`, and which require complete materialization?
4. How do dynamic regions, measurements, add-ons, and exports declare their
   structural data requirements?
5. Do structural edits invalidate the source, create a new generation, or force
   materialization?
6. How are sequential-only and random-access MolSysMT forms represented?
7. How are multiple canvas consumers with different current structures served
   without duplicating scientific authority?

## Evidence required

- audit every direct `_molsys` use by topology-only, current-structure,
  arbitrary-structures, complete-system, and mutation requirements;
- prototype against native `MolSys`, XTC/DCD, and H5MSM sources;
- benchmark many atoms/few structures, few atoms/many structures, and a combined
  realistic case;
- prove exact ordering, units, selection mapping, failure behavior, and resource
  cleanup;
- specify public API and add-on compatibility before implementation.

## Non-goals for 1.0

This document does not authorize partial residency, cache eviction, structure
window requests, interpolation, or changes to `view.molsys` before the contract
questions above are resolved.
