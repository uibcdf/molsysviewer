# Selections

MolSysViewer delegates selections to MolSysMT.

A *selection* is an expression that identifies atoms (and related topology items)
from the currently loaded molecular system.

## When you use selections

Selections appear in viewer operations such as:

- `view.hide(selection)`
- `view.show(selection)`
- `view.isolate(selection)`
- `view.zoom(selection)`
- `view.new_region(selection, ...)`

## Syntax

Selections are parsed by MolSysMT when `syntax="MolSysMT"` (the default).
Keep selection expressions consistent with your MolSysMT workflow.

If you already use MolSysMT, you can reuse the same selection strings here.
