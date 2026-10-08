# Complete open-issue reconciliation — 2026-10-07

This review covers **all 34 issues open at its start**, not just the bug queue.
It compares their current claims with maintained contracts, current owners and
already verified source/public-artifact evidence. It does not certify the eventual
1.0 artifact or prove the absence of every unreported defect. Snapshot facts and
the installed form-detection probe are in [the receipt](open_issue_reconciliation_20261007.json).

## What still belongs before 1.0

1. Finish public documentation and first-contact review against the actual API
   and installed candidate. This review repairs the pip/backend/platform claims
   in #95/#97, not every tutorial or public promise.
2. Complete the separate central Python 3.14 admission in #93. The public
   scientific pair is already qualified; remote suite.toml still says authorized.
   Supply its immutable public receipt to the owner of uibcdf/molsyssuite#29/#51.
3. Build/qualify an exact candidate that contains source-only Movie #177 and
   style isolation #149 fixes. Public 0.24.0 does not contain those fixes.
   Preserve all failed attempts and accepted evidence; run the final mandatory
   source, hosted core, installed public/staging and citation/release gates on
   the eventual candidate and dependencies.
4. Decide the final supported Interactions compatibility boundary and freeze the
   public API. A shipped experimental baseline alone is not a 1.0 commitment.

No unresolved core functional defect is established by the **reviewed issue
set** after the scoped closures below. That statement does not cover unreported
faults, broad scale/GPU behavior or the final installed artifact. Experimental Qt
still has real unresolved observations/defects; keep them visible outside the core
gate. Central guide refresh and tooling/advisory work retain their own owners.

## Full board inventory

The disposition column records the accepted scope, which may be more precise
than an old issue title or its unset milestone. Open issue bodies are immutable
between opening and closing under the local reporting protocol; maintained
reports and this inventory carry updated analysis. Existing post-1.0 milestones
stay in force. No old publication, remote/Qt certification or provider source
change is implied by this review.

| Issue | Disposition | Remaining action or delivered evidence | Owner / record |
| --- | --- | --- | --- |
| [#152](https://github.com/uibcdf/molsysviewer/issues/152) | Resolved | Portable guide already published at d0d5ea85; later canonical-guide refresh/adoption remains separate. | [Viewer guide publication; later central sync](archive/ackredit_portable_guide_publication.md) |
| [#115](https://github.com/uibcdf/molsysviewer/issues/115) | Post-1.0 | Mol* dependency update, imported-API review and exact core qualification; retain the current pin for 1.0. | [Viewer frontend](pending_proposals/post_1.0/update_molstar_dependency.md) |
| [#113](https://github.com/uibcdf/molsysviewer/issues/113) | Post-1.0 | Future supported Qt candidate: exact native artifacts and visible-window workflows; no core gate. | [Viewer / native Qt providers](pending_proposals/post_1.0/recheck_latest_conda_forge_qt_for_standalone.md) |
| [#109](https://github.com/uibcdf/molsysviewer/issues/109) | Experimental; outside core gate | Canonical binding selection is implemented; current Qt/WebGL evidence still fails on some environments. Do not certify it from import/solver success. | [Viewer Qt host](pending_proposals/migrate_standalone_qt_to_canonical_pyside6_6_11_2.md) |
| [#100](https://github.com/uibcdf/molsysviewer/issues/100) | Remote growth; outside core gate | Core/portable/render-worker lanes exist and core is qualified. Portable remote and managed GPU completion retain independent candidate requirements; exclusion is not a pass. | [Viewer E2E / GPU host](pending_proposals/post_1.0/reproducible_browser_and_render_worker_e2e_evidence.md) |
| [#97](https://github.com/uibcdf/molsysviewer/issues/97) | Resolved | Public core, experimental native hosts and remote preview are distinguished consistently; addressable docs guard. | [Viewer public distribution contract](archive/clarify_linux_only_standalone_qt_support.md) |
| [#95](https://github.com/uibcdf/molsysviewer/issues/95) | Resolved | Remove unsupported public pip install/update commands; correct backend/addon and Windows claims. | [Viewer user setup](archive/public_pip_installation_promise.md) |
| [#93](https://github.com/uibcdf/molsysviewer/issues/93) | Pre-1.0 administrative receiving | Public pair 16/16 and source 3.14 gates are delivered. Remote suite registry still says authorized; obtain central admission. Qt has separate owners. | [Viewer + uibcdf/molsyssuite#29/#51](pending_proposals/extend_python_support_to_3_14.md) |
| [#89](https://github.com/uibcdf/molsysviewer/issues/89) | Superseded by maintainer | Do not recover historical npm 0.20.1/0.22.0/0.23.0; preserve missing-runtime caveat and future publication verification. | [Viewer release operator](archive/historical_npm_runtimes_superseded.md) |
| [#82](https://github.com/uibcdf/molsysviewer/issues/82) | Superseded by maintainer | Do not backfill Releases/Zenodo for 0.22.0/0.23.0; retain tags. Verified 0.24.0 supersedes that release work. | [Viewer release operator](archive/historical_github_releases_superseded.md) |
| [#80](https://github.com/uibcdf/molsysviewer/issues/80) | Upstream tooling; outside core gate | External pytest-xdist report remains prepared, not sent. Requires explicit authorization for the third-party submission; not a reproduced current core defect. | pytest-xdist / explicit submission decision |
| [#78](https://github.com/uibcdf/molsysviewer/issues/78) | Resolved | Retain 219 quarantined modules outside installed/runtime package for 1.0; no deletion or restoration. | [Viewer digestion contract](archive/quarantined_digesters_await_a_decision.md) |
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
| [#39](https://github.com/uibcdf/molsysviewer/issues/39) | Post-1.0 on demand | Classic-script shared runtime for opening a many-view bundle directly from disk; current served/shared and self-contained HTML remain separate supported routes. | [Viewer HTML/runtime](pending_proposals/classic_script_runtime_for_offline_bundles.md) |
| [#36](https://github.com/uibcdf/molsysviewer/issues/36) | Post-1.0 experimental defect | Qt orbit export lacks a returned camera snapshot; retain the defect instead of treating core camera/movie tests as Qt closure. | [Viewer Qt camera/export](pending_bugs/post_1.0/standalone_qt_movie_camera_snapshot.md) |
| [#35](https://github.com/uibcdf/molsysviewer/issues/35) | Experimental defect; outside core gate | Live replacement fix and automated guards exist; ten visible-window replacements and Ready/no-delivery-error confirmation remain unperformed. | [Viewer Qt / manual GPU observation](pending_bugs/standalone_qt_live_demo_reload.md) |

## Publication and retention decisions

Diego explicitly declines historical backfill in #82/#89: close as superseded
by verified 0.24.0, preserving old tags and acknowledging missing old artifacts.
Require exact npm workflow completion and independent public npm/CDN, Conda/pair
and Zenodo verification for every future release. This is operator discipline,
not a claim that continuous publication monitoring has been implemented.

Retain #78's 219 developer-only quarantined modules for 1.0; no files are deleted
or restored. #152's original portable-guide publication already occurred; the
later expanded canonical Ackredit guide must use central guarded synchronization,
without importing new runtime features into this closure.

#42's historical seven-minute extension-detection bottleneck is repaired in the
installed public provider. The measured detector still peaks at roughly one
payload allocation; do not claim that the complete pipeline is constant-memory.
The absent explicit source-form hint remains a provider enhancement and eventual
benchmark cleanup, not a current core 1.0 blocker.

The original issue snapshots and qualification receipts keep their original
versions and scope. No package, tag, npm upload, promotion or Release is created
by this reconciliation.

## Local validation and integration

The new installation/host contract passes five first targeted cases. The complete
selected public-docs/README/reporting/link check then passes 193 cases with one
honest omission (ElastNetMT addon not installed). Sphinx builds with warnings as
errors; it does not execute notebooks. No complete scientific suite, Qt/GPU
certification or new artifact qualification is claimed by these documentation
checks. Remote #178 test-resource ownership commits are integrated unchanged;
its offscreen/cleanup evidence is distinct from visible-window host validation.

Seven real npm/version-resolution guards also pass. These cover the repaired
version-source and publication-injection failure mechanisms; no permanent
publication monitoring or historical backfill is introduced.

## Confirmed board closeout

Issues #78/#82/#89/#95/#97/#152 are CLOSED with the published decisions and
records from `a59c9692`. The board has 28 remaining open issues; all 27 active
queue documents agree with it. The board-only external report #80 remains open.
Exact-head policy `37734137505`, Conda governance `37734137627` and actual
notebook execution `37734136842` pass. The broader scientific/core/source-pair
runs retain their current native statuses in the receipt; this closeout is not
final 1.0 certification. No publication was dispatched by this task.
