# Molecular system

In MolSysSuite, a **molecular system** has:

- a **topology** (atoms, bonds, residues, chains, etc.), and
- one or more **structures** (spatial information: coordinates, optional periodic box, optional time).

This matters because MolSysViewer is driven by MolSysMT concepts such as `selection` and `structure_indices`.

```{toctree}
:hidden:
:maxdepth: 2

loading
selections
navigation_between_structures
```

## Terminology

Molecular system
: Topology + `structures`.

Structure
: One set of coordinates (and optional `box`/`time`). In other libraries this is often called a “frame”. In MolSysSuite, a structure can also represent a model (not necessarily time-ordered).

Structure indices
: Which structures you are working with (for example, to pick a subset from a trajectory-like dataset).

Selection
: A MolSysMT selection expression used to pick atoms/residues from the molecular system.
