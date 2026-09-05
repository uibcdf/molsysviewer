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

| Capability | Public API | Public | Digested | Provenance | Docs | Evidence | Status | Since |
|---|---|---:|---:|---|---|---|---|---|
| Whole | `view.whole.` | 15 | 11 | MolSysViewer (Python authority) | [page](../docs/content/user/scene_management/whole.md) | contract-tested, browser-observed | stable | 0.5.0 |
| Regions | `view.regions.`, `view.regions[…].` | 44 | 42 | MolSysViewer (Python authority) | [page](../docs/content/user/scene_management/regions.md) | contract-tested, browser-observed | stable | 0.1.0 |
| Layers | `view.layers.` | 12 | 12 | MolSysViewer (Python authority) | [page](../docs/content/user/scene_management/layers.md) | contract-tested, browser-observed | stable | 0.1.0 |
| Selections and active selection | `view.selections.`, `view.active_selection.` | 21 | 21 | MolSysMT (scientific authority) | [page](../docs/content/user/scene_management/selections.md) | contract-tested, browser-observed | stable | 0.9.0 |
| Representations, styles and presets | `view.styles.`, `view.whole.set_representation` | 35 | 35 | Mol* (rendering authority) | [page](../docs/content/user/representations/types.md) | contract-tested, browser-observed | stable | 0.18.0 |
| Annotations | `view.annotations.` | 22 | 21 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/labels.md) | contract-tested, browser-observed | stable | 0.9.0 |
| Measurements | `view.measurements.` | 20 | 20 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/measurements.md) | contract-tested, browser-observed | stable | 0.9.0 |
| Shapes | `view.shapes.` | 50 | 36 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/shapes/index.md) | contract-tested, browser-observed | stable | 0.1.0 |
| Trajectories and frames | `view.player.` | 11 | 11 | MolSysViewer (Python authority) | [page](../docs/content/user/movie/playback.md) | contract-tested, browser-observed, benchmarked | stable | 0.18.0 |
| Trajectory plot | `view.trajectory_plot.` | 4 | 4 | MolSysViewer (Python authority) | [page](../docs/content/user/overlays/trajectory_plot.md) | contract-tested, browser-observed | experimental | 0.19.0 |
| Movie | `view.movie.` | 13 | 13 | MolSysViewer (Python authority) | [page](../docs/content/user/movie/export.md) | contract-tested, browser-observed | experimental | 0.18.0 |
| Camera | `view.camera.`, `view.get_camera_snapshot`, `view.set_camera_snapshot`, `view.zoom` | 11 | 11 | Frontend (mirrored to Python) | [page](../docs/content/user/viewer/camera_and_controls.ipynb) | contract-tested, browser-observed | stable | 0.18.0 |
| save_state / load_state | `view.save_state`, `view.load_state`, `view.export_state`, `view.import_state` | 4 | 4 | MolSysViewer (Python authority) | [page](../docs/content/user/export/state.md) | contract-tested | stable | 0.19.0 |
| save_session / load_session | `view.save_session`, `molsysviewer.load_session` | 2 | 2 | MolSysViewer (Python authority) | [page](../docs/content/user/export/session.md) | contract-tested | experimental | 0.22.0 |
| HTML export and replay | `view.export.` | 5 | 5 | MolSysViewer (Python authority) | [page](../docs/content/user/export/index.md) | contract-tested, browser-observed | stable | 0.9.0 |
| Popup | `view.build_popup_scene_snapshot` | 1 | 1 | MolSysViewer (Python authority) | [page](../docs/content/developer/standalone_surfaces.md) | contract-tested, browser-observed, benchmarked | stable | 0.20.1 |
| Remote sessions | `molsysviewer.remote.` | 4 | 0 | MolSysViewer (Python authority) | [page](../docs/content/user/remote/index.md) | contract-tested, browser-observed | experimental | 0.23.0 |
| Standalone (Qt host) | `molsysviewer.launch_standalone_qt0`, `molsysviewer.create_standalone_qt0_window` | 2 | 0 | MolSysViewer (Python authority) | [page](../docs/content/developer/standalone_surfaces.md) | contract-tested, browser-observed, benchmarked, human-observed | experimental | 0.19.0 |
| Add-ons | `molsysviewer.addons.`, `view.addons.` | 54 | 54 | Add-on (external owner) | [page](../docs/content/developer/addons.md) | contract-tested, browser-observed | stable | 0.10.0 |
| MolSysMT integration | `view.extract`, `view.whole.get`, `view.whole.convert`, `view.regions[…].get`, `view.regions[…].convert` | 7 | 3 | MolSysMT (scientific authority) | [page](../docs/content/user/introduction/molsysmt.md) | contract-tested, browser-observed | stable | 0.19.0 |
| Units | `molsysviewer.config.set_default_standard_units` | 1 | 1 | PyUnitWizard (unit authority) | [page](../docs/content/user/introduction/units.md) | contract-tested | stable | 0.5.0 |

## What a row cannot hold

- **Regions** — A region survives serialisation as the recipe that produced it, not as an index list.
- **Selections and active selection** — Selection syntax is MolSysMT's; MolSysViewer digests and forwards it.
- **Representations, styles and presets** — Type names map 1:1 to Mol* built-ins. `label`, `orientation` and `plane` are deliberately not types; see the types page.
- **Trajectory plot** — Observed drawing since 2026-09-05: the card, one polyline per series with a point per frame, and the labels the caller asked for.
- **Movie** — Playback observed drawing since 2026-09-05: the camera passes through intermediate positions, lands on the last keyframe, and stops short when interrupted. Export stays out -- it depends on an external encoder and is not exercised in CI.
- **Camera** — The snapshot is the frontend's state mirrored back, and is None on a view that never rendered. Contract S9 holds camera authority.
- **save_state / load_state** — The scene and the vantage point it was saved from: no molecular system and no history. Records the structure it was written from, and re-resolves onto a different one rather than replaying indices that mean other atoms. Version 2 refuses version 1 rather than migrating it.
- **save_session / load_session** — A `.msv` bundle carrying the molecular system alongside the state, so it reopens with nothing loaded first. No size budget: a session is as large as its trajectory.
- **Remote sessions** — The count is four because the walk inventories instances rather than classes, and the eleven classes in `__all__` are constructed by the host rather than held by a user. The surface a user actually types is the `molsysviewer-server` console script declared in `pyproject.toml`, and its page is the row's documentation. Client-side rendering is exercised by `remote-client-rendering.e2e.ts`. Server-side rendering was first certified on spika on 2026-09-05 by `remote-session.e2e.ts`, using WebGL2 with `ANGLE (NVIDIA Corporation, NVIDIA GeForce GTX 1080/PCIe/SSE2, OpenGL ES 3.2)` (uibcdf/molsysviewer#84). This is evidence for that host, not a claim that every deployment has a working GPU path. The zero in `Digested` is measured, not missing: none of the four takes a digested argument. This is the first time the inventory baseline has left zero on that count, tracked in uibcdf/molsysviewer#83, and it is Phase 10's open public-callable digestion item rather than a defect in this row. Experimental is the page's own word: the Python API, command-line options, transport protocol and deployment configuration may change.
- **Standalone (Qt host)** — Transport is pinned by contract. Since 2026-09-02 the `qt-pipeline` CI job asserts under Xvfb that the pipeline completes -- bridge ready, payload served, structure loaded through software WebGL. That is not the render being correct: nothing reads the framebuffer, and #64 is the standing proof the two differ. A real GPU and a visible window remain unobserved.
- **Add-ons** — MolSysViewer owns the host contract; each toolkit owns and ships its integration. Maturity is declared per add-on.
- **MolSysMT integration** — Digestion is MolSysMT's; only the caller named in an error is ours. `contains` and `is_composed_of` were removed -- `get` answers both (`get(n_waters=True) > 0`, and the set of `molecule_type`) and `msm.*` still has them. See uibcdf/molsysviewer#71.
- **Units** — Physical magnitudes are quantities, never bare numbers.

## Nothing has watched these draw

No E2E suite opens these in a browser and asserts what appeared. For a viewer
that is the sharpest gap there is, and it is why `browser-observed` exists as
a label rather than as a number in a column:

- save_state / load_state
- save_session / load_session
- Units

One of them is already `experimental` and say so. `save_state / load_state` and `Units` are `stable`, which is defensible — none of them draws anything — but it is the kind of claim that should be made on purpose rather than inherited.

## Declared `stable` without drawing anything

These do not render. `browser-observed` is not a label they are missing, it is
one they can never earn, and the ladder reading of these labels is what makes
that look like a gap. Each says why the level is deserved anyway, so the claim
is made on purpose rather than inherited:

- **save_state / load_state** — Nothing about it is rendered: it writes a JSON document and reads one back. Its contract is version 2 refusing version 1, and the re-resolution onto a different structure -- both checked by contract tests, neither visible on a screen.
- **Units** — A policy about argument values, enforced before anything reaches the frontend. There is no pixel it could be watched producing.

## Two columns, two questions

**Evidence** answers *how do we know it works*. The labels are independent, not a
ladder: a capability may be benchmarked and never browser-observed.

**They live here and nowhere else.** Four of the five are derived from what this
audit already knows, and a hand-written label elsewhere would be an assertion --
the thing this table exists to replace. No devguide document describes a
capability: all nineteen capability pages are in `docs/`. A devguide document
without an evidence label is not making a weaker claim, it is making a different
kind of claim. Decided in `uibcdf/molsysviewer#61`; the record is
`devguide/archive/evidence_labels_beyond_the_capability_audit.md`.

- `implemented` — the code path exists and is reachable from the public API
- `contract-tested` — Python tests exercise the documented behaviour
- `browser-observed` — an E2E suite drives it in a real browser and asserts what it drew
- `benchmarked` — a reproducible benchmark records environment and methodology
- `human-observed` — someone has watched it on a real screen

Adapted from MolSysMT's `DOCUMENT_POLICY.md`. Their `Parity-tested` and
`Scientifically validated` are not here: both are their questions — comparing
equivalent forms, comparing against an independent oracle. A viewer renders what
MolSysMT computes, so the equivalent question is whether anyone watched it draw.

This is a different axis from `verification` in
[`reporting_protocol.md`](reporting_protocol.md), which qualifies how well a
*report* was checked rather than how well a *capability* is verified.

**Status** answers *may I depend on it*.

- `stable` — the public surface is documented, digested and covered by tests, and
  changing it is a deliberate act.
- `experimental` — it works and is used, and one of documentation, browser-level
  coverage or environment independence is missing. The note says which.
- `roadmap` — declared and not implemented. No row is in this state today; the
  value exists so that a future one cannot be quietly recorded as `experimental`.

A capability is not `stable` merely because it has no known defect. It is stable
when someone else could depend on it and find out from us before it changed.

