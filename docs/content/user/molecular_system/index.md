# Molecular system

This section is the practical core of how MolSysViewer works.

In a live viewer, open **Studio > Load** to load a file or PDB ID. Load is the
first Studio section and opens by default in an empty view. Choose independent
systems to combine several sources, or complementary files for a topology and
its coordinates or trajectory. **Add to whole**, **Replace whole** and
**Append structures of the current system** make the intended operation explicit.
Paths must be accessible to the running Python session. Structures defaults to
`0` (the first frame); enter `all` to load a complete trajectory.

After loading, Studio opens **System** for inspection, unless you have already
chosen another section. Return to **Load** to add another source. A failed load
keeps the form and its values so you can correct them. Browser-only exported
views offer inspection of their saved content without Python-backed loading.

MolSysViewer builds on MolSysMT, so the way you load, query, and modify what you see in the viewer follows MolSysMT’s definition of a molecular system: a topology (atoms, groups, chains, bonds, ...) plus one or more structures (coordinates, optional box, optional time).

If you are new to these ideas, start with the first section, an overview on what a molecular system is for MolSysViewer, and then continue in order:

Why this matters: `new_view` defaults to `load_mode="selection"`, so a selection subsets the system you load. Use `load_mode="all"` when you want the full system and a visible region tagged `selection`.

```{toctree}
:maxdepth: 1

molecular_system
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
