# Closed audits

These are dated investigations retained as evidence for current contracts and
regression guards. Findings marked closed must not be treated as open work.

- [`python_js_boundary_audit_2026_07.md`](python_js_boundary_audit_2026_07.md)
- [`standalone_qt_audit_2026_07.md`](standalone_qt_audit_2026_07.md)
- [`standalone_qt_event_transport_diagnostic.md`](standalone_qt_event_transport_diagnostic.md)
- [`import_cost_and_lazy_loading.md`](import_cost_and_lazy_loading.md)
- [`pre_1_0_phases_5_6_8_9_10_audit_2026_08.md`](pre_1_0_phases_5_6_8_9_10_audit_2026_08.md)
  — the independent audit that closed Phases 5, 6, 8, 9 and the Phase 10 persistence
  slice on 2026-08-09, with one mutation per mechanism. It closes nothing of Phase 7.
- [`unused_imports_2026_09.md`](unused_imports_2026_09.md)
  — 264 `F401` reports, 60 of them real. Records why the other 204 stand, and how deleting
  one import from the `_smonitor.py` config module left every diagnostic in the package
  firing with the right class and an empty message. Guarded by
  `tests/test_catalog_templates_render.py`.

Two documents here are inventories rather than audits, and they are the evidence record
of the 2026-08 pre-1.0 round. Their execution order is superseded by
[`../pre_1_0_architecture_rework_and_hardening_master_plan.md`](../pre_1_0_architecture_rework_and_hardening_master_plan.md),
and each marks its own items closed in place:

- [`open_items_after_the_2026_08_smoke_round.md`](open_items_after_the_2026_08_smoke_round.md)
  — sixteen of nineteen closed. The three that remain need a person, not work, and are
  collected in [`../what_needs_a_human_2026_08.md`](../what_needs_a_human_2026_08.md).
- [`transport_popup_audit_followups_2026_08.md`](transport_popup_audit_followups_2026_08.md)
  — items 1 to 9 done or measured; 10 to 12 are standing boundaries rather than work.
