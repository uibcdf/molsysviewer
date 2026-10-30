# Open-issue reconciliation — 2026-10-13

This inventory covers all **33 issues open at the snapshot**, including the new
#245. It reconciles issue ownership and accepted scope with current contracts;
it does not certify an installed candidate. Issue bodies stay unchanged between
opening and closing. The [receipt](open_issue_reconciliation_20261013.json)
retains the exact board snapshot and scoped evidence.

## Before the next candidate freeze

- **#245:** source and exact hosted core qualification are complete. The
  window-owned addon fix passes the actual receiving guard and core 43/43. The old hosted
  browser and Linux Python 3.14 source-pair campaigns fail at the same real
  Render-after-popup-close assertion; neither is called green.
- **#233:** corrected at 4d15a410; 14 real metadata/import/clear cases and 13
  affected workspace cases pass. Exact hosted source receiving is complete at 4d15a410.
- **#242:** compatible remediation returns zero advisories with Mol* 5.4.1
  preserved; the actual runtime passes 43/43 core browser suites. #115 stays post-1.0.
- Retain completed applicable source CI; resume the postponed PHMT/Jupyter smoke and central
  Python admission #93. Qt's separate experimental failures are retained.
- Finish public documentation and human first contact, then explicitly freeze
  an authorized 0.25.0 producer and qualify its installed artifacts. Existing
  0.24.0 public and superseded 0.24.1 evidence cannot qualify the new source.

Both 1.0 publications remain paused. There is no tag, package or promotion
operation in this reconciliation. The prior review's October 7 claim about its
reviewed issue set does not cover subsequently reported #233/#239/#242/#245.

## Full board inventory

| Issue | Disposition | What remains or was delivered | Owning record |
| --- | --- | --- | --- |
| [#245](https://github.com/uibcdf/molsysviewer/issues/245) | Resolved; exact hosted core approved | Independent window lifecycle and owner-specific actions implemented; local Python/JS/browser guards pass. Exact-source hosted core is approved: six Python cells, three Python 3.14 hosts and 43/43 browser suites. | [Record](archive/addon_popup_panel_lifecycle.md) |
| [#242](https://github.com/uibcdf/molsysviewer/issues/242) | Resolved in source | Nine affected packages repaired; clean audit has zero findings, Mol* 5.4.1 preserved and live/offline audit guards required. | [Record](archive/locked_javascript_dependency_advisories.md) |
| [#239](https://github.com/uibcdf/molsysviewer/issues/239) | Resolved in source | c9471fe3 consumes trajectory summaries. Real Python/widget/Mol* guard now requires 17 fps in original and popup and rejects the unknown-op warning. | [Record](archive/widget_trajectory_summary_dispatch.md) |
| [#233](https://github.com/uibcdf/molsysviewer/issues/233) | Resolved in source | Type exports no longer discover partial providers; exact deferred sources and explicit registry clear are guarded with 27 final import/workspace cases. | [Record](archive/addon_entrypoint_partial_initialization.md) |
| [#226](https://github.com/uibcdf/molsysviewer/issues/226) | Post-1.0; explicitly deferred | Copy equivalent Python from Studio is the maintainer's explicit remaining UI deferral. | [Record](pending_proposals/post_1.0/studio_copy_python.md) |
| [#115](https://github.com/uibcdf/molsysviewer/issues/115) | Post-1.0 | Mol* dependency update, imported-API review and exact core qualification; retain the current pin for 1.0. | [Viewer frontend](pending_proposals/post_1.0/update_molstar_dependency.md) |
| [#113](https://github.com/uibcdf/molsysviewer/issues/113) | Post-1.0 | Future supported Qt candidate: exact native artifacts and visible-window workflows; no core gate. | [Viewer / native Qt providers](pending_proposals/post_1.0/recheck_latest_conda_forge_qt_for_standalone.md) |
| [#109](https://github.com/uibcdf/molsysviewer/issues/109) | Experimental; outside core gate | Canonical binding selection is implemented; current Qt/WebGL evidence still fails on some environments. Do not certify it from import/solver success. | [Viewer Qt host](pending_proposals/migrate_standalone_qt_to_canonical_pyside6_6_11_2.md) |
| [#100](https://github.com/uibcdf/molsysviewer/issues/100) | Post-1.0 remote preview | Core/portable/remote/server-GPU lane contracts exist. Managed remote qualification remains deferred. The old issue has no milestone; accepted local scope takes precedence without rewriting its open body. | [Record](pending_proposals/post_1.0/reproducible_browser_and_render_worker_e2e_evidence.md) |
| [#93](https://github.com/uibcdf/molsysviewer/issues/93) | Delivered support; central admission pending | Existing public Python 3.11–3.14 evidence remains valid. The current central suite.toml still records authorized, not admitted; old central implementation text is not a new missing Viewer feature. | [Record](archive/extend_python_support_to_3_14.md) |
| [#80](https://github.com/uibcdf/molsysviewer/issues/80) | External reporting decision; outside core gate | Viewer workaround is delivered. Reporting to third-party pytest-xdist is still a separate unapproved decision. | [Record](pending_proposals/pytest_xdist_receiver_thread_report.md) |
| [#59](https://github.com/uibcdf/molsysviewer/issues/59) | Post-1.0 | Advanced pocket/void/channel/interface representations beyond shipped primitives and shape providers. | [Viewer shapes / scientific provider](pending_proposals/post_1.0/visualization_representations_roadmap.md) |
| [#58](https://github.com/uibcdf/molsysviewer/issues/58) | Post-1.0 | Add a terminal pixel presentation; existing pixel/export tools are not a shipped terminal viewer. | [Viewer terminal host](pending_proposals/post_1.0/viewing_in_the_terminal.md) |
| [#57](https://github.com/uibcdf/molsysviewer/issues/57) | Post-1.0 | Generated static typing for assembled mixins; do not infer that runtime validation supplies type stubs. | [Viewer / ArgDigest typing](pending_proposals/post_1.0/viewer_mixin_contract_and_caller_resolution.md) |
| [#56](https://github.com/uibcdf/molsysviewer/issues/56) | Post-1.0 growth; baseline delivered | Minimal Studio Interactions is shipped and qualified. Remaining richer source modes, analytics and dynamic workflows only. | [Viewer Studio](pending_proposals/post_1.0/studio_interactions_subpanel_ui_design.md) |
| [#55](https://github.com/uibcdf/molsysviewer/issues/55) | Post-1.0 | Lazy/windowed trajectory residence changes view.molsys semantics; 1.0 retains complete selected-structure materialization and its size guard. | [Viewer data plane / MolSysMT](pending_proposals/post_1.0/structure_windowing_and_lazy_materialization.md) |
| [#54](https://github.com/uibcdf/molsysviewer/issues/54) | Post-1.0 | Further topology encoding/residency/Qt join performance; existing measured ceilings are not arbitrary-scale certification. | [Viewer performance](pending_proposals/post_1.0/representative_scale_followups.md) |
| [#53](https://github.com/uibcdf/molsysviewer/issues/53) | Post-1.0 | Receiver-owned structure barrier for endpoints beyond the current sender contract. | [Viewer message transport](pending_proposals/post_1.0/receiver_side_structure_barrier.md) |
| [#52](https://github.com/uibcdf/molsysviewer/issues/52) | Post-1.0 | Automated native Qt framebuffer/workflow check on a qualified GPU runner; prior manual evidence is not broad host support. | [Viewer Qt / runner provisioning](pending_proposals/post_1.0/qt_render_check_on_a_gpu_runner.md) |
| [#51](https://github.com/uibcdf/molsysviewer/issues/51) | Post-1.0 | Qt popout parity; live Jupyter popouts do not certify the separate Qt shell. | [Viewer Qt host](pending_proposals/post_1.0/qt_popout_parity.md) |
| [#50](https://github.com/uibcdf/molsysviewer/issues/50) | Post-1.0 ideas | External terminal-viewer ideas remain an inventory, not accepted 1.0 functionality. | [Viewer product planning](pending_proposals/post_1.0/proteinview_external_review_and_ideas.md) |
| [#49](https://github.com/uibcdf/molsysviewer/issues/49) | Post-1.0 | Multiple synchronized viewports; progressive multi-source loading is already delivered and is a different capability. | [Viewer canvas](pending_proposals/post_1.0/multiview_split_screen.md) |
| [#48](https://github.com/uibcdf/molsysviewer/issues/48) | Post-1.0 growth; baseline delivered | Native analyses, nine families, queries, geometry, H5MSM/session and minimal Studio are delivered. Additional formats, persistence/residence analytics and dynamic evaluation remain. | [Viewer Interactions / MolSysMT](pending_proposals/post_1.0/interactions_domain.md) |
| [#47](https://github.com/uibcdf/molsysviewer/issues/47) | Post-1.0 cold review | Export-rework design tradeoffs to revisit on evidence; not a blanket assertion that current export paths fail. | [Viewer export](pending_proposals/post_1.0/export_rework_rough_edges.md) |
| [#46](https://github.com/uibcdf/molsysviewer/issues/46) | Post-1.0 enriched metadata | SDF/protein composition and hierarchy fixes #312/#313 are delivered. Preserve the distinct enhanced chemical metadata/schema review; successful load alone does not prove every enrichment. | [MolSysMT schema / Viewer bridge](pending_proposals/post_1.0/chemical_metadata_loss_sdf_pdb.md) |
| [#45](https://github.com/uibcdf/molsysviewer/issues/45) | Post-1.0 | User-configurable atom/group/chain picking granularity; current supported selection actions remain qualified. | [Viewer picking](pending_proposals/post_1.0/canvas_picking_level.md) |
| [#44](https://github.com/uibcdf/molsysviewer/issues/44) | Post-1.0 | Richer MVS annotation behavior beyond the current supported anchors/lifecycle. | [Viewer annotations / Mol*](pending_proposals/post_1.0/annotations_mvs_machinery.md) |
| [#43](https://github.com/uibcdf/molsysviewer/issues/43) | Post-1.0 tooling | Measure non-pytest output token costs; no scientific/runtime capability depends on completing that study. | [Viewer developer tools](pending_proposals/post_1.0/agent_token_cost_of_non_pytest_tests.md) |
| [#42](https://github.com/uibcdf/molsysviewer/issues/42) | Provider API improvement; outside core gate | Published 0.23.0 repairs extension detection; measured 95k-atom detection 2.319 s. Explicit source hint still absent, provider #151 open; benchmark-only direct import remains. | [uibcdf/molsysmt#151 / Viewer benchmark](pending_proposals/molsysmt_known_source_form_and_large_string_detection.md) |
| [#41](https://github.com/uibcdf/molsysviewer/issues/41) | Advisory; outside core gate | Historical documentation-pipeline analysis offered to MolSysMT; a provider migration is not a promised Viewer feature. | [MolSysMT docs / explicit advisory follow-up](pending_proposals/molsysmt_docs_pipeline_analysis.md) |
| [#39](https://github.com/uibcdf/molsysviewer/issues/39) | Post-1.0 on demand | Existing board deferral remains explicit; retain its legacy path for immutable archived backlinks. Single self-contained HTML and served shared bundles retain their supported routes. | [Record](pending_proposals/classic_script_runtime_for_offline_bundles.md) |
| [#36](https://github.com/uibcdf/molsysviewer/issues/36) | Post-1.0 experimental defect | Qt orbit export lacks a returned camera snapshot; retain the defect instead of treating core camera/movie tests as Qt closure. | [Viewer Qt camera/export](archive/standalone_qt_movie_camera_snapshot.md) |
| [#35](https://github.com/uibcdf/molsysviewer/issues/35) | Experimental defect; outside core gate | Live replacement fix and automated guards exist; ten visible-window replacements and Ready/no-delivery-error confirmation remain unperformed. | [Viewer Qt / manual GPU observation](archive/standalone_qt_live_demo_reload.md) |

## Queue corrections and preserved observations

#233/#239/#242 had open board reports without local queue entries; they now have
records with their original evidence scope. #80's optional external-reporting
decision also has an explicit local owner. #39 was already post-1.0 on the board; its legacy path is retained because
immutable archived documents link there. No feature was newly deferred.

#48/#56 own growth beyond the delivered experimental Interactions baseline,
not a missing base API or Studio panel. #45 still owns broader configurable
picking granularity. Old sketches do not override current public contracts.
#42's provider source-form hint remains open in uibcdf/molsysmt#151; the historical
large-string detection bottleneck is already repaired. #35/#36/#109 retain
experimental Qt defects/observations outside the supported core gate.

The independent dependency audit observes nine transitive advisories. It does
not prove an exploit in Viewer; excluding all nine as tooling would also be
incorrect because Immutable is used by the real Mol* state tree.

## Source closures

#245 and #239 have fixes and passing guards with archived records. Issue-board
closure is independently verified after reviewed source integration at 19d92c25. The 33-issue table
retains the initial snapshot; it does not mean these two still require a code fix.
The 19d92c25 required hosted campaign is approved. Later #233/#242 and the
newly found #246 are resolved at 4d15a410, with archived guards. Their fresh exact
hosted campaign passes all required core gates; the human smoke remains postponed.

After #233/#242/#246 closure, the current board contains **29 open issues and
29 local queue records**, with no
missing owner record. The preceding 19d92c25 source CI passes all required core gates: six Python regression
cells, three Python 3.14 hosts and 43/43 core browser suites, plus lint, policy,
notebooks and Conda governance. Experimental Qt fails separately; the
[lifecycle receipt](addon_window_lifecycle_validation_20261013.json) preserves
its independent scope. No installed-package or live-Jupyter result is inferred.

## Additional hardening / approved providers

The [new receiving receipt](addon_discovery_dependency_validation_20261013.json)
records canonical SMonitor 0.20.0 build 1 / DepDigest 0.15.1 build 0 adoption in
development and all #233/#242/#246 scopes. The single full local Python run
retains three clear-related failures; 27 final affected cases and a final real
popup guard pass after correction. Runtime/lockfile browser core passes 43/43
before the final Python clear correction. Fresh exact hosted qualification passes six regression cells, three Python
3.14 hosts, official core 43/43 and 25/25 notebooks; Qt remains a separate failure; these are source results, not installed candidate or live Jupyter gates.
