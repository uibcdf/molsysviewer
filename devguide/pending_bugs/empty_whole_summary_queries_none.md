---
summary: Empty Whole summaries query MolSysMT with None and emit eight startup errors.
issue: uibcdf/molsysviewer#323
status: partial
opened: 2026-11-07
closed:
severity: low
verification: reproduced
area: [regions, studio, standalone, diagnostics]
guard: tests/test_empty_whole_summary.py
normative:
blocked_by: []
supersedes: []
---

# Empty Whole summary calls

**Corrected in working source; headless/affected Python and automated native Qt
receiving pass; integration pending.** The initial actual Qt #319 receiving passes its
four functional capture/restore cases, but stderr retains eight
`get_form(None)` errors. Independent headless `sys.setprofile` observations
localize all eight calls to empty standalone HTML construction, without
replacing provider functions. Imports, demo loading/extraction, empty View
construction and `export_state` do not produce them in that probe.

The real chain is `standalone.build_standalone0_html(None, output_filename)`
through `popup_snapshot._build_panel_snapshot` and
`regions._whole_summary_record` to `msm.get(None)` and `get_form(None)`.
The composition-count loop checks that a system exists; the subsequent eight
`contains` probes do not. Catching their exceptions happens after MolSysMT has
already reported an invalid input. Viewer owns the invalid call; no scientific
provider correction or diagnostic suppression is appropriate.

Keep the existing valid empty-summary schema/count semantics and absolute
shapes. Empty and shape-only snapshots must not query a nonexistent molecular
system. Real loaded-system probes and their scientific results retain their
existing behavior. Add headless real-call-flow guards, standalone/snapshot
construction and loaded-demo controls; receive the affected native startup
without treating earlier retained errors as newly absent.

The complete four-page live duplicate review contains 321 issue/PR records
before #323. Closed #233 concerns addon discovery; #286 concerns Load usability.
Neither records this empty-summary caller. Private originals are
`A5-empty-form-1/observations.json` and `A5-empty-form-receipt-1.json` in the
approved task evidence. Original stderr and all eight call stacks remain
retained. No fixed-code, installed-package or complete host-health claim is
made by this record.

The causal guard first fails three actual empty/shape-only/standalone cases
with 24, 24 and eight invalid form queries, while two controls pass. The fix
preserves the eight zero counts and queries only an existing system. All five
direct cases then pass; the broader affected selection passes **107 cases**,
with four native Qt cases explicitly deselected. Loaded pentalanine retains
62 atoms, seven groups and one peptide; absolute geometry remains at
`[10, 20, 30]` angstrom with a 2 angstrom radius and unchanged portable state.
The observer forwards/restores an existing profiler instead of replacing
scientific behavior. See the [source receipt](../empty_whole_summary_receiving_20261107.json).
The subsequent actual-display Qt guard passes four capture/perturbed-camera
and frame-restore cases on the corrected source, with zero occurrences of the
eight invalid `get_form(None)` errors. It checks real Wayland/NVIDIA WebGL2,
responsive GUI execution and Cancel before any draw; all 4,341 selected inputs
remain unchanged and all owned processes terminate. The existing GBM fallback
and D-Bus observations remain in stderr; this is not a globally error-free host
claim. The private `A5-native-durable-verification-2.json` retains the receipt.
Reviewed delivery and consolidated acceptance remain pending. Previous native
success retains its eight observed errors as historical evidence; later camera
protocol changes need their own affected receiving.

The fourth durable native run additionally receives the final shared camera
runtime: native exit 0, all 4,341 selected inputs unchanged, zero unsupported
`None` queries and zero process survivors. Its four captured/restored files and
before-draw Cancel also pass; GBM/D-Bus observations remain explicit. Reviewed
delivery and consolidated acceptance still have their separate conditions.
