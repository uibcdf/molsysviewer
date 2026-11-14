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

### Being worked on (4)

- [`recovered_canvas_initial_structure_observation.md`](recovered_canvas_initial_structure_observation.md) — [#354](https://github.com/uibcdf/molsysviewer/issues/354) — Diagnose a recovered Jupyter canvas staying at structure zero after eight successful cycles. *(medium, measured)*
- [`source_guards_utf8_recurrence.md`](source_guards_utf8_recurrence.md) — [#169](https://github.com/uibcdf/molsysviewer/issues/169) — New native-source guards reintroduce platform-dependent text decoding. *(medium, reproduced)*
- [`updated_annotation_pick_receiving_timeout.md`](updated_annotation_pick_receiving_timeout.md) — [#325](https://github.com/uibcdf/molsysviewer/issues/325) — Updated annotation GPU pick times out in hosted canvas-popup receiving. *(medium, measured)*
- [`windows_movie_webm_encoder.md`](windows_movie_webm_encoder.md) — [#385](https://github.com/uibcdf/molsysviewer/issues/385) — WebM needs explicit native codec selection and Windows receiving. *(medium, reproduced)*

### Partially done (11)

- [`direct_state_rejection_erases_scene.md`](direct_state_rejection_erases_scene.md) — [#317](https://github.com/uibcdf/molsysviewer/issues/317) — Rejected direct state imports erase existing scene objects before validation finishes. *(high, reproduced)*
- [`empty_whole_summary_queries_none.md`](empty_whole_summary_queries_none.md) — [#323](https://github.com/uibcdf/molsysviewer/issues/323) — Empty Whole summaries query MolSysMT with None and emit eight startup errors. *(low, reproduced)*
- [`failed_factory_retains_owned_view.md`](failed_factory_retains_owned_view.md) — [#316](https://github.com/uibcdf/molsysviewer/issues/316) — Failed new_view initialization retains its unreturned View and widgets. *(medium, reproduced)*
- [`nested_jupyter_receiving_provenance.md`](nested_jupyter_receiving_provenance.md) — [#364](https://github.com/uibcdf/molsysviewer/issues/364) — Qualify the molecular sources actually imported by nested Jupyter receiving. *(medium, reproduced)*
- [`qt_file_dialog_absolute_path_typing.md`](qt_file_dialog_absolute_path_typing.md) — [#287](https://github.com/uibcdf/molsysviewer/issues/287) — Native Qt file-dialog guard types while its modal window is inactive. *(medium, reproduced)*
- [`retired_notebook_molecular_data.md`](retired_notebook_molecular_data.md) — [#356](https://github.com/uibcdf/molsysviewer/issues/356) — Identify why closed notebook controllers retain molecular data during repeated real work. *(medium, measured)*
- [`standalone_html_retains_owned_view.md`](standalone_html_retains_owned_view.md) — [#324](https://github.com/uibcdf/molsysviewer/issues/324) — Standalone HTML construction retains internally created Views and widget registrations. *(medium, reproduced)*
- [`trajectory_plot_numeric_precision.md`](trajectory_plot_numeric_precision.md) — [#321](https://github.com/uibcdf/molsysviewer/issues/321) — Trajectory labels hide nonzero values and narrow-offset axes lose numerical precision. *(medium, reproduced)*
- [`trajectory_plot_pixel_dimensions.md`](trajectory_plot_pixel_dimensions.md) — [#322](https://github.com/uibcdf/molsysviewer/issues/322) — Trajectory plot pixel dimensions are digested as CSS and fail in the public API. *(medium, reproduced)*
- [`trajectory_plot_seek_skips_python_authority.md`](trajectory_plot_seek_skips_python_authority.md) — [#314](https://github.com/uibcdf/molsysviewer/issues/314) — Trajectory plot navigation changes the canvas without updating Python structure state. *(high, reproduced)*
- [`view_close_failure_blocks_cleanup.md`](view_close_failure_blocks_cleanup.md) — [#318](https://github.com/uibcdf/molsysviewer/issues/318) — A provider panel close error prevents remaining View resources from closing. *(medium, reproduced)*

### Open (2)

- [`hosted_popup_context_menu_receiving.md`](hosted_popup_context_menu_receiving.md) — [#305](https://github.com/uibcdf/molsysviewer/issues/305) — Diagnose the hosted popup context-menu timeout after fullscreen controls receiving. *(medium, upstream)*
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
