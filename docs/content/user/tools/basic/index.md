# Basic tools

`molsysviewer.tools.basic` contains broadly useful composition helpers.

This module is limited to pure composition/subsetting helpers that return a new
`MolSysView` without mutating the input viewer.

Use `molsysmt.*(view, ...)` for molecular-system reads. Use the MolSysMT addon
namespace, `view.addons.molsysmt.basic.*`, for live molecular edits on an
existing viewer.

```{toctree}
:maxdepth: 1

extract.md
copy.md
concatenate_structures.md
merge.md
```
