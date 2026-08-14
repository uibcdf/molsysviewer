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

- [`exported_view_background_not_transparent_when_loaded_dark.md`](exported_view_background_not_transparent_when_loaded_dark.md):
  a view exported with `background="transparent"` is opaque white when the embedding
  page is dark at load time, and never recovers. Reported from MolSysMT's published
  documentation. Located in `applyExportedBackground`, which resolves light/dark and
  calls `toggleBackground` even in transparent mode, where neither is meaningful.
- [`standalone_qt_live_demo_reload.md`](standalone_qt_live_demo_reload.md):
  replacing a loaded demo does not update the real Qt scene. It requires a real
  Qt/WebGL window for the next diagnostic pass.

The movie camera-snapshot defect is confirmed but explicitly deferred under
[`post_1.0/`](post_1.0/README.md).

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

The former color-digester finding is resolved: `value_range.py` and
`replace.py` exist, their public surfaces are covered by
`tests/test_argdigest_public_api.py`, and the obsolete bug file is no longer
present.

## Recommended execution

The active Qt report is one real-window validation block:

1. Reproduce each defect separately in the supported Qt/WebGL environment.
2. Add temporary, runtime-only diagnostics at both sides of the bridge. Record
   message/generation identifiers and acknowledgements; do not add diagnostic
   events to scene history or export.
3. Identify the first boundary where the expected state disappears.
4. Add the narrow automated regression test at that boundary.
5. Confirm the corrected workflow in the real window before closing the bug.

Fakes remain useful for the regression after the cause is known. They are not
evidence that the original real-window symptom is fixed.

No other bug work should be invented from stale plans. New dogfooding findings
enter this directory only with a reproduction and an affected public contract.
