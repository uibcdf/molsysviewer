# MolSysMT

MolSysViewer builds on top of [MolSysMT](https://www.uibcdf.org/molsysmt).

MolSysMT is the part of MolSysSuite that defines what a *molecular system* is, how it can be represented in different forms, and how you can query it. In practice, this is what makes features like selection strings, element levels (atom/group/molecule/...), and structure indexing feel consistent across the suite.

MolSysViewer does not invent its own definition of a molecular system. Instead, it adopts MolSysMT's model and uses it everywhere:

- When you load data, MolSysViewer relies on MolSysMT to interpret topology and structures.
- When you write selections, MolSysViewer relies on MolSysMT to parse and evaluate them.
- When you call helpers like `view.get(...)`, `view.info(...)`, or `view.select(...)`, you are using MolSysMT concepts through a viewer-oriented API.

If you are new to these ideas, the best starting point is:

- {doc}`../molecular_system/molecular_system`
