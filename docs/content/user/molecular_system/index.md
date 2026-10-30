# Molecular system

This section is the practical core of how MolSysViewer works.

In a live viewer, open **Studio > Load** to load a file or PDB ID. Load is the
first Studio section and opens by default in an empty view. Enter a PDB ID or
file path, or use **Browse…** to choose files. Choosing files fills the inputs;
the **Load system** button performs the load. You can also press Enter in an
input. The action and result stay available while you scroll through sources.

Browse explores the machine running Python. In Jupyter it offers folders,
multiple selection, hidden files and pages of entries. In Qt it opens the native
file dialog. With remote Jupyter, upload local files to Jupyter or copy them to
the server before browsing them here; a browser-local path does not identify a
file on the server.

Use **Add source** for more inputs. Choose **Independent systems** to combine
several systems, or **Complementary files** for a topology and its coordinates
or trajectory. Source **Options** disclose labels, atom selection and structure
indices. They default to all atoms and structure `0` (the first frame); enter
`all` to load a complete trajectory, or an ordered list such as `0, 8, 3`.
Combining several trajectories requires explicit structure pairing.

Once a system is loaded, choose **Add to Whole**, **Replace Whole** or
**Append structures**. The primary button names the operation. Append requires
an existing system; it accepts a single system, including complementary files.

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
