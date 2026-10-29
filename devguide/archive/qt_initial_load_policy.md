---
summary: Qt launchers ignore load_mode=all and discard unselected atoms
issue: uibcdf/molsysviewer#274
status: resolved
opened: 2026-10-29
closed: 2026-10-29
severity: high
verification: reproduced
area: [standalone, loading]
guard: tests/test_new_view.py::test_host_replacement_uses_factory_loading_policy
normative:
blocked_by: []
supersedes: []
---

# Qt initial loading loses the full-system policy

**Reported:** final standalone source review, 2026-10-29.

## What

With the real dialanine demo, `new_view(demo.molsys, selection=[0, 1],
load_mode="all")` retains 22 atoms and creates a visual selection region.
`create_standalone_qt0_window(demo, selection=[0, 1], load_mode="all")`
instead retains only two atoms and creates no region. This removes molecular
data despite the caller's explicit full-system request.

## How

The persistent Qt host calls `view.load(selection=selection, mode="replace")`
unconditionally, ignoring the accepted `load_mode`. The corrected seam shares
the factory's private initial-loading policy; Qt retains explicit replacement.
Invalid visual selections are checked through MolSysMT before replacement.
Public signatures and the factory's add-mode loading remain unchanged.

## Why

Both launchers promise the same molecular selection semantics. Retaining the
whole system matters for subsequent selection and exploration in Studio.

## What was refuted

This is not a rendering-only discrepancy: the native window's Python MolSys
itself has two atoms. A restricted-sandbox Qt display abort is separate from
the defect; the same real-window probe outside the sandbox reaches Ready and
reproduces the atom-count difference.

## Resolution

The shared private loading policy now governs the factory and persistent Qt
host. The guard tests both selected-atom loading and full-system retention,
including region replacement. Adjacent guards check invalid selections before
replacement and the empty-selection fallback. Forty-three related Python
contracts pass. The real Qt workbench guard passes on the native Linux desktop
and explicit X11/SwiftShader; it checks full-system retention, its inherited
selection region and nonconsecutive structures [8, 0, 3] in a second host.
Public loading signatures are unchanged. This resolves the source defect;
the standalone remains experimental, with platform/artifact gates separate.
