# Basic tools

`molsysviewer.tools.basic` contains broadly useful composition helpers.

This module now mixes two kinds of viewer-centric helpers:

- **functional wrappers** over `MolSysView` methods, for users who prefer a MolSysMT-like style;
- **pure composition/subsetting helpers** that return a new `MolSysView`.

```{toctree}
:maxdepth: 1

select.md
get.md
info.md
extract.md
set.md
remove.md
add.md
append_structures.md
contains.md
is_composed_of.md
copy.md
compare.md
concatenate_structures.md
merge.md
```
