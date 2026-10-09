# Basic tools

`molsysviewer.tools.basic` contains broadly useful composition helpers.

This module is limited to pure composition/subsetting helpers that return a new
`MolSysView` without mutating the input viewer.

Use `molsysmt.*(view, ...)` for molecular-system reads. Compute molecular
edits with MolSysMT and load the resulting system with `view.load(molsys,
mode="replace")`. Advanced callers can reconcile edits with
`view.apply_system_edit(...)` and explicit index maps. MolSysMT is the native
backend; its former addon namespace has been retired.

```{toctree}
:maxdepth: 1

extract.md
copy.md
concatenate_structures.md
merge.md
```
