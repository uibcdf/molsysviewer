# Capability audit

**Generated — do not edit by hand.** Run
`python devtools/capability_audit.py --write`; the judgement lives in
`devtools/capability_audit.py`, everything else is read from the repository.

One row per capability, so that README, the documentation, the paper and a
release cannot make slightly different claims about the same thing. `Public` and
`digested` count the public callables of that surface; `Since` is the first tag
containing the commit that added its anchor module, read from git rather than
remembered.

`Provenance` answers what the paper needs: whether MolSysViewer *decides* the
behaviour, delegates it, or merely hosts it.

| Capability | Public API | Public | Digested | Provenance | Docs | Unit | E2E | Status | Since |
|---|---|---:|---:|---|---|---:|---:|---|---|
| Whole | `view.whole.` | 16 | 13 | MolSysViewer (Python authority) | [page](../docs/content/user/scene_management/whole.md) | 2 | 1 | stable | 0.5.0 |
| Regions | `view.regions.`, `view.regions[…].` | 45 | 45 | MolSysViewer (Python authority) | [page](../docs/content/user/scene_management/regions.md) | 4 | 3 | stable | 0.1.0 |
| Layers | `view.layers.` | 12 | 12 | MolSysViewer (Python authority) | [page](../docs/content/user/scene_management/layers.md) | 2 | 2 | stable | 0.1.0 |
| Selections and active selection | `view.selections.`, `view.active_selection.`, `view.select` | 29 | 29 | MolSysMT (scientific authority) | — | 2 | 2 | stable | 0.8.0 |
| Representations, styles and presets | `view.styles.`, `view.whole.set_representation` | 35 | 35 | Mol* (rendering authority) | [page](../docs/content/user/representations/types.md) | 3 | 1 | stable | 0.18.0 |
| Annotations | `view.annotations.` | 22 | 21 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/labels.md) | 1 | 2 | stable | 0.8.0 |
| Measurements | `view.measurements.` | 20 | 20 | MolSysViewer (Python authority) | — | 1 | 2 | stable | 0.8.0 |
| Shapes | `view.shapes.` | 50 | 36 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/shapes/index.md) | 3 | 2 | stable | 0.1.0 |
| Trajectories and frames | `view.player.` | 11 | 11 | MolSysViewer (Python authority) | [page](../docs/content/user/movie/playback.md) | 2 | 2 | stable | 0.18.0 |
| Trajectory plot | `view.trajectory_plot.` | 4 | 4 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/trajectory_plot.md) | 2 | 0 | experimental | 0.19.0 |
| Movie | `view.movie.` | 13 | 13 | MolSysViewer (Python authority) | [page](../docs/content/user/movie/export.md) | 1 | 0 | experimental | 0.18.0 |
| Camera | `view.camera.`, `view.get_camera_snapshot`, `view.set_camera_snapshot`, `view.zoom` | 11 | 11 | Frontend (mirrored to Python) | — | 2 | 1 | stable | 0.18.0 |
| save_state / load_state | `view.save_state`, `view.load_state`, `view.export_state`, `view.import_state` | 4 | 4 | MolSysViewer (Python authority) | — | 3 | 0 | stable | 0.19.0 |
| HTML export and replay | `view.export.` | 5 | 5 | MolSysViewer (Python authority) | [page](../docs/content/user/export/index.md) | 4 | 2 | stable | 0.9.0 |
| Popup | `view.build_popup_scene_snapshot` | 1 | 1 | MolSysViewer (Python authority) | [page](../docs/content/developer/standalone_surfaces.md) | 4 | 3 | stable | 0.20.1 |
| Standalone (Qt host) | `molsysviewer.launch_standalone_qt0`, `molsysviewer.create_standalone_qt0_window` | 2 | 0 | MolSysViewer (Python authority) | [page](../docs/content/developer/standalone_surfaces.md) | 2 | 1 | experimental | 0.19.0 |
| Add-ons | `molsysviewer.addons.`, `view.addons.` | 54 | 54 | Add-on (external owner) | [page](../docs/content/developer/addons.md) | 2 | 1 | stable | 0.10.0 |
| MolSysMT integration | `view.get`, `view.contains`, `view.is_composed_of`, `view.convert`, `view.extract` | 15 | 15 | MolSysMT (scientific authority) | [page](../docs/content/user/introduction/molsysmt.md) | 3 | 1 | stable | 0.19.0 |
| Units | `molsysviewer.config.set_default_standard_units` | 1 | 1 | PyUnitWizard (unit authority) | [page](../docs/content/user/introduction/units.md) | 2 | 0 | stable | 0.5.0 |

## Capabilities with no user documentation page

Implemented and undocumented is a different state from experimental, so the
status column does not absorb it. These have a public API and tests, and a
reader has nowhere to be sent:

- Selections and active selection
- Measurements
- Camera
- save_state / load_state

## What a row cannot hold

- **Regions** — A region survives serialisation as the recipe that produced it, not as an index list.
- **Selections and active selection** — Selection syntax is MolSysMT's; MolSysViewer digests and forwards it.
- **Representations, styles and presets** — Type names map 1:1 to Mol* built-ins. `label`, `orientation` and `plane` are deliberately not types; see the types page.
- **Trajectory plot** — No E2E suite opens it in a browser.
- **Movie** — Export depends on an external encoder and is not exercised in CI.
- **Camera** — The snapshot is the frontend's state mirrored back, and is None on a view that never rendered. Contract S9 holds camera authority.
- **save_state / load_state** — Semantic scene state only: no molecular system, camera or history. Version 2 refuses version 1 rather than migrating it.
- **Standalone (Qt host)** — Transport is pinned by contract; the render path has no automated observation on a real GPU and visible window.
- **Add-ons** — MolSysViewer owns the host contract; each toolkit owns and ships its integration. Maturity is declared per add-on.
- **MolSysMT integration** — Delegates with `skip_digestion=True`, so argument names are normalised on this side.
- **Units** — Physical magnitudes are quantities, never bare numbers.

## Reading the status column

- `stable` — the public surface is documented, digested and covered by tests, and
  changing it is a deliberate act.
- `experimental` — it works and is used, and one of documentation, browser-level
  coverage or environment independence is missing. The note says which.
- `roadmap` — declared and not implemented. No row is in this state today; the
  value exists so that a future one cannot be quietly recorded as `experimental`.

A capability is not `stable` merely because it has no known defect. It is stable
when someone else could depend on it and find out from us before it changed.

