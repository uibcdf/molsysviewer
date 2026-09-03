# MolSysMT

MolSysViewer builds on top of [MolSysMT](https://www.uibcdf.org/molsysmt).

MolSysMT is the part of MolSysSuite that defines what a *molecular system* is, how it can be represented in different forms, and how you can query it. In practice, this is what makes features like selection strings, element levels (atom/group/molecule/...), and structure indexing feel consistent across the suite.

MolSysViewer does not invent its own definition of a molecular system. Instead, it adopts MolSysMT's model and uses it everywhere:

- When you load data, MolSysViewer relies on MolSysMT to interpret topology and structures.
- When you write selections, MolSysViewer relies on MolSysMT to parse and evaluate them.
- When you call helpers like `view.get(...)`, `view.info(...)`, or `view.select(...)`, you are using MolSysMT concepts through a viewer-oriented API.

## The methods a view borrows from MolSysMT

Five viewer methods are MolSysMT questions asked of the system a view is showing. They take
MolSysMT's own argument names, so what you know from `msm` transfers directly.

### Asking what the system holds

`view.get(...)` reads attributes, and `view.info(...)` prints the summary table. Two more
answer yes or no, and the difference between them is worth having straight:

```python
view = msv.demo["1TCD"]

view.contains(protein=True)                    # True  — there is protein in it
view.is_composed_of(protein=True)              # False — but it is not *only* protein
view.is_composed_of(protein=True, water=True)  # True  — protein and water is all of it
view.contains(lipid=True)                      # False — no lipid at all
```

`contains` asks *is any of this here*. `is_composed_of` asks *is this all there is*.

### Taking part of it somewhere else

Both narrow a system down; they differ in what you get back.

```python
molsys = view.convert(to_form="molsysmt.MolSys")           # a MolSysMT object
protein = view.extract(selection='molecule_type=="protein"')  # another view
```

`convert` hands the system to MolSysMT in one of its forms, for analysis that has nothing
to do with drawing. `extract` returns **a new `MolSysView`** holding just the selected part
— a second viewer, not a value. Reach for `convert` when you are leaving the viewer, and
for `extract` when you want to keep looking.

Both accept `selection` and `structure_indices`, so either can narrow in space and in time
at once.

## Where to read next

If you are new to these ideas, the best starting point is:

- {doc}`../molecular_system/molecular_system`
- {doc}`../molecular_system/get` — `view.get` in depth
- {doc}`../tools/basic/extract` — `extract` as a scene operation
