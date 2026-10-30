# Pending Bugs

Every entry is filed and closed under [`../reporting_protocol.md`](../reporting_protocol.md):
it carries front matter, is tracked by a GitHub issue, and closes only when it names the
test that fails if the defect returns.

This directory contains confirmed or reproducible defects that affect current
MolSysViewer behavior. Bug reports are evidence and implementation queues, not
future API proposals.

Each report should state the affected public contract, reproduction, cause,
recommended correction, and acceptance tests. Move resolved reports to an
archive only after the implementation and regression tests are complete.

## Current triage

Entries are rendered from each report's front matter — edit the reports, not this
list.

<!-- generated: devguide_index -->

### Being worked on (2)

- [`qt_status_presentation.md`](qt_status_presentation.md) — [#279](https://github.com/uibcdf/molsysviewer/issues/279) — Qt status severity, lifetime and full-text access are inconsistent. *(medium, reproduced)*
- [`qt_window_geometry_restore.md`](qt_window_geometry_restore.md) — [#280](https://github.com/uibcdf/molsysviewer/issues/280) — Qt persists expanded dimensions as the normal window size. *(medium, reproduced)*

### Partially done (1)

- [`standalone_qt_live_demo_reload.md`](standalone_qt_live_demo_reload.md) — [#35](https://github.com/uibcdf/molsysviewer/issues/35) — In the standalone Qt host, replacing the loaded demo leaves the previous system on screen. *(high, measured)*

### Open (1)

- [`qt_dbus_conda_prefix_address.md`](qt_dbus_conda_prefix_address.md) — [#278](https://github.com/uibcdf/molsysviewer/issues/278) — Qt startup reports an invalid D-Bus system address in Conda prefixes containing @. *(low, reproduced)*

<!-- /generated -->

The Qt movie camera-snapshot defect is resolved in source; its evidence is
preserved in [the archive](../archive/standalone_qt_movie_camera_snapshot.md).

The camera zoom-out defect (Contract S9) was resolved and archived on 2026-08-05.
The upstream report was filed as
[molstar/molstar#1903](https://github.com/molstar/molstar/issues/1903), accepted
and implemented upstream, and is retained as historical evidence in
[`../archive/report_molstar_empty_scene_camera_bounds.md`](../archive/report_molstar_empty_scene_camera_bounds.md).
The upstream fix is not released yet, so the local S9 protection remains.

Two reports were resolved on 2026-08-04 by the export rework and moved to
[`../archive/`](../archive/README.md): the docs-lite views pinned to an
unpublished npm version, and the standalone export mutating live widget state.
Both disappeared as consequences of collapsing the two export templates into one,
not as separate patches.

The headless-Chrome entry was **withdrawn** on 2026-09-06 and moved to
[`../archive/`](../archive/README.md). Nothing was fixed: command-line Chrome on that
machine still will not navigate to `http://`. It left this queue because the queue is for
defects affecting current MolSysViewer behaviour, and after
[#81](https://github.com/uibcdf/molsysviewer/issues/81) moved the three colour tests to
the TypeScript E2E suite it affects none. `withdrawn` is the status that does not demand a
`guard`, and no test of ours can watch a browser we do not control.

The former color-digester finding is resolved: `value_range.py` and
`replace.py` exist, their public surfaces are covered by
`tests/test_argdigest_public_api.py`, and the obsolete bug file is no longer
present.

## Recommended execution

#35 needs the maintainer's ten-load visual confirmation using the current
native host and its Ready status. Its automated native-desktop and hosted
pixel checks pass; see [the current review](../standalone_review_20261029.md).
Receive the manual observation before closing it. Add runtime-only diagnostics
if that observation exposes a remaining defect; the fixed transport does not
need another speculative investigation. Automated pixels and software Xvfb
results do not substitute for the requested human confirmation.

No other bug work should be invented from stale plans. New dogfooding findings
enter this directory only with a reproduction and an affected public contract.
