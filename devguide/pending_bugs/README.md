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

### Being worked on (1)

- [`qt_load_dialog_completion_readiness.md`](qt_load_dialog_completion_readiness.md) — [#287](https://github.com/uibcdf/molsysviewer/issues/287) — Observe readiness and completion of native Qt file-dialog actions in CI *(medium, reproduced)*

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

#35's ten-replacement visual confirmation is received and the report is
[archived](../archive/standalone_qt_live_demo_reload.md). The remaining #278
entry concerns the local Conda D-Bus address and is not a core 1.0 blocker.

No other bug work should be invented from stale plans. New dogfooding findings
enter this directory only with a reproduction and an affected public contract.
