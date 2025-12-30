# Molecular system

In MolSysSuite, a **molecular system** has:

- a **topology** (atoms, groups, chains, bonds, etc.), and
- one or more **structures** (spatial information: coordinates, optional periodic box, optional time).

This matters because MolSysViewer is driven by MolSysMT concepts such as `selection` and `structure_indices`.

```{toctree}
:hidden:
:maxdepth: 2

loading_and_inspect
topology
structures
info
selection
get
set
remove
add
append_structures
```

## Terminology

Molecular system
: Topology + `structures`.

Structure
: One set of coordinates (and optional `box`/`time`). If the structures come from a molecular dynamics trajectory, many libraries call each structure a “frame”. In MolSysSuite, a structure can also represent a model (not necessarily time-ordered).

Structure indices
: Which structures you are working with (for example, to pick a subset from a trajectory-like dataset).

Selection
: A MolSysMT selection expression used to pick atoms/groups from the molecular system.
