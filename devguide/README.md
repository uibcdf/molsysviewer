# Developer guide

`devguide/` contains the repository's engineering contracts, current planning,
implementation references, and explicitly deferred work. It is not a changelog:
Git and `docs/content/developer/changes_notes.md` already preserve chronology.

## Read first

For a new session aimed at 1.0, begin with the
[current handoff](checkpoints.md#resume-in-one-page), then its
[ordered next actions](checkpoints.md#what-is-next) and the
[1.0 release plan](path_to_1_0.md). The middle of the checkpoint
retains dated evidence: do not interpret earlier candidate coordinates
as current instructions. Read the active report for the chosen work item;
the experimental Qt-host migration is `uibcdf/molsysviewer#109`, and
the deferred version/dogfooding decision is `uibcdf/molsysviewer#113`.
The shared Linux Python 3.14 development recipe is maintained by
`uibcdf/molsyssuite#52`.

For feature placement and product scope, first apply
[`core_and_addon_boundary.md`](core_and_addon_boundary.md). It is normative for
the core visualization/add-on tools boundary; runtime availability is separate.

Use these documents in this order:

1. [`scene_contracts.md`](scene_contracts.md) is normative for scene state,
   regions, whole, color ownership, ordering, persistence, and scene objects.
   [`studio_interaction_contract.md`](studio_interaction_contract.md) specifies
   Studio navigation, lifecycle, native backend ownership and export delivery.
2. [`engineering_rules.md`](engineering_rules.md) defines implementation and
   verification rules.
3. [`session_reproducibility.md`](session_reproducibility.md) applies whenever
   user-created state is introduced.
4. [`architecture.md`](architecture.md) and
   [`digestion_and_dependencies.md`](digestion_and_dependencies.md) describe the
   Python/TypeScript boundary and the supporting UIBCDF tooling.
5. [`checkpoints.md`](checkpoints.md) starts with the current handoff and
   links to the ordered next actions. Its dated evidence is context,
   not a new release gate.
6. [`release_and_citation.md`](release_and_citation.md) defines the DOI, Zenodo,
   `CITATION.cff`, and post-release verification lifecycle.

When documents disagree, the contracts and current code win over plans, vision
documents, and historical audits.

## Current status and planning

- **System composition received in source — 2026-10-28:** provider `71fbe4f46d3c70e4e973c8025f01752a8c9b1084` adds
  `basic.add`, `append_structures`, `merge` and `concatenate_structures`.
  Bound destination edits use explicit managed prefix maps; collection inputs and
  independent results remain explicit. Source exposure is 144/244 paths (basic
  25/26), plus two separately counted FASTA readers. The receiving record retains
  52 directed checks, the quota-interrupted regression and selective recovery,
  new owner-source receiving and the test-only native #522 correction. Native
  #520 partial append remains open. Host `4e1bf764` corrects a test's unsupported
  0.23.0 in-place assumption; all eight growth checks pass with both current
  source and the minimum public native package. Hosted qualification remains in
  progress; Qt remains experimental. See [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#system-composition-received-in-source--2026-10-28).
  No installed-artifact qualification, package or 1.0 publication is claimed.

- **Basic maps and explicit file tools received in source — 2026-10-28:**
  provider 9f6e2e011 adds eleven expert methods. Basic 21/26 and H5MSM 7/7 bring
  scoped exposure to 140/244; two raw FASTA readers are counted separately.
  All 41 directed / 6,024 joint cases and 65 guide blocks / 305 doctests pass;
  source/backend hashes and raw notebook schemas stay unchanged. Original
  9f6e2e011 smoke/devguide runs are cancelled; four auxiliary controls pass.
  Successor 1f0bef212 smoke 40754038881 passes 4,028 native / 2,395 addon
  cases with sixteen/four optional skips; all its triggered controls pass.
  Another 600 affected checks pass on that successor. See [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#basic-maps-and-explicit-file-tools-received-in-source--2026-10-28).
  No core/GUI/dependency/package change or 1.0 publication is introduced.

- **Canonical interaction expert paths complete in source — 2026-10-28:**
  provider b0f21e58d110e7447b1cdccc3eea421675c67222 adds the four remaining families: 15/15 canonical paths,
  131/244 inventoried callable paths. All 133 directed cases, a frozen 5,840-case
  regression, 1,004 current-source checks and 61/279 current examples pass.
  Native uibcdf/molsysmt#515 full-suite failures and uibcdf/molsysmt#516 selector limitations remain visible;
  all six hosted source controls later pass, including 4,028 native / 2,354
  addon smoke cases with sixteen/four optional-provider skips. See
  [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#canonical-interaction-expert-paths-completed-in-source--2026-10-28).

- **Three chemical contact families — 2026-10-27:** provider 24ee46486fec5c19da847a61229f553f5200921e
  adds ionic, hydrophobic and halogen detection. All 76 directed / 4,915 joint
  regression cases, 57 guide blocks / 241 inherited examples and 32 package
  guards pass. Inventory: 127/244 paths, interactions 11/15. Five source controls
  pass; original smoke 40618125703 is cancelled. Later 2083a105b source
  passes its separate smoke. See
  [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#ionic-hydrophobic-and-halogen-detector-families-received--2026-10-27).

- **Expert interaction detectors — 2026-10-27:** provider 8d129124e adds
  three hydrogen-bond detectors and canonical disulfide candidates. All 65
  directed / 4,710 joint regression cases and 54 guide blocks / 214 inherited
  examples pass. Inventory: 124/244 paths, interactions 8/15. Native supplied
  donors are tracked in uibcdf/molsysmt#511. Five source controls pass;
  scientific smoke 40613617586 passes with 3,595 native / 2,142 addon cases
  and thirteen/four optional-provider skips. See
  [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#expert-hydrogen-bond-and-disulfide-detectors-received--2026-10-27).

- **Hydrogen-bond sites and directions — 2026-10-27:** provider b50edcc52 adds
  four explicit nested expert tools, independently of core visualization. All
  44 directed / 4,536 regression cases and 52 guide blocks / 184 inherited
  examples pass. Inventory: 120/244 paths, interactions 4/15. Native limits
  are uibcdf/molsysmt#506, #507, #508 and #509. Five exact-source controls pass;
  scientific smoke 40608186286 is cancelled without a completed addon tier. See
  [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#build-source-ci-completed-and-hydrogen-bond-sites-received--2026-10-27).

- **Eleven native build audits — 2026-10-27:** provider 11e7ab7f0 adds eight
  explicit readers without molecular repair or scene updates. All 62 directed
  cases, one frozen 4,414-case joint regression, 50 guide blocks and 163 inherited
  examples pass. Inventory: 116/244 inspected paths, build 11/30. Native
  multi-structure solvation is uibcdf/molsysmt#504; CIP metadata remains #503.
  Five source controls pass; main smoke 40598293439 is cancelled at installation.
  Fixed-ref recovery 40598751459 passes 3,431 native / 2,033 addon cases, with
  fifteen optional Ackredit skips. See
  [receiving](pending_proposals/molsysmt_tools_addon_receiving.md#eleven-build-audits-received-in-source--2026-10-27).

- **Complete physchem / initial build — 2026-10-27:** provider 511fafb54 exposes
  all 34 reviewed physchem paths and three build diagnostics. The full expert
  final inventory finds 108 exposed / 244 inspected callable paths, including
  aliases/utilities and two native MD stubs; broader modules remain. The 40 + 18 new directed cases
  pass. A 4,283-case regression has one corrected packaging-allowlist failure;
  32 packaging/command/inventory and 115 help follow-ups pass, with 49 guide
  blocks / 155 inherited examples. Corrected CI 40585977458 passes with
  3,365 native / 1,971 addon cases and fifteen optional Ackredit skips; five
  other controls pass. Tooling-only inventory completion is 4e544cb12. See the
  [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#complete-physchem-and-initial-build-tools--2026-10-27).

- **Explicit chemical readers — 2026-10-27:** provider 636003965 exposes
  AutoDock typing, CIP and explicit partial-charge calculations: 28 of 34
  reviewed physchem paths. All 3,819 regression cases (69 new directed cases)
  and 45 guide blocks / 109 inherited examples pass. Prior source CI closes
  uibcdf/molsysmt#500/#501 and #499 has 80 directed receiving passes. Native
  uibcdf/molsysmt#503 remains a nested-reference ownership limit. New-source
  CI 40580219002 fails on an orphan test-file command; its full-list repair is
  received in the next phase. See the
  [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#explicit-chemical-readers-received--2026-10-27).

- **Bound molecular descriptors — 2026-10-27:** provider ea9fff339 exposes
  lipophilicity and receives all seven native TPSA/descriptor contribution
  levels. The source facade has 25 of 34 reviewed physchem exports. All 122
  directed cases, the frozen 3,589-case regression and 43 guide blocks / 98
  inherited examples pass. The
  [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#lipophilicity-and-descriptor-contributions-received--2026-10-27)
  retains output/context maps, H attribution and scientific limits. Native
  hierarchy repairs pass directed receiving. Follow-up 4ad988584 fixes two
  fixtures (210 cases) and raises the CI budget under uibcdf/molsysmt#500/#501.
  Earlier timeout and failed runs stay non-success evidence; corrected-source
  CI 40575948453 passes with its recorded optional skips and pre-repair #499
  xfail; #500/#501 are closed. GUI and installed qualification remain separate.

- **Molecular TPSA addon reader — 2026-10-27:** provider f55d7c2f7 exposes
  the native molecule-level descriptor with explicit states/variant and optional
  provenance report. The facade has 24 wrappers; the latest committed native
  inventory has 34 after lipophilicity was added. All 53 directed cases, 3,294
  frozen regression cases, 158 incoming-refactor checks and 41 guide blocks / 94
  inherited examples pass with their distinct scopes. Both exact source CI runs
  pass (2,645 native / 1,718 addon cases, five optional Ackredit skips each). The
  [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#molecular-tpsa-receiving--2026-10-27)
  keeps native #494/#495 limits, overlapping owner work and installed/GUI scope
  separate. The previous Viewer E2E 40454434547 passes 44/44 on 386ed937.

- **Reference-scale addon readers — 2026-10-26:** provider `efc9b94f3` adds
  bulkiness and required-category secondary-structure propensity mirrors. The
  source facade exposes 23 of 33 inspected physchem functions, with native
  quantities/arrays and explicit scientific limits preserved. The
  [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md#bulkiness-and-propensity-mirrors-received--2026-10-26)
  separates the 3,144-case frozen regression from 596 incoming-source checks;
  all six exact-source controls pass (2,576 native / 1,666 addon cases,
  three optional Ackredit skips). GUI/installed qualification remain separate.

- **Core/add-on product boundary approved — 2026-10-22:**
  [the normative decision](core_and_addon_boundary.md) defines core as molecular
  visualization/exploration, including qualified calculations directly creating
  visual content. Additional preparation, editing, general analysis and domain
  tools belong to add-on/scientific interfaces. A redesigned MolSysMT tools
  add-on has experimental source `basic` readers, independent outputs,
  retained-axis edits/synchronization, eleven `topology` readers and eighteen
  `structure` calculations and managed native translation/rotation/reflection, rigid fitting, explicit centering, single-structure displacement, principal-axis alignment and both dihedral editors, plus thirteen PBC tools
  and thirty-four physchem source wrappers plus eleven build diagnostics, including TPSA/lipophilicity, contribution levels, chemical typing/stereo/charge and independent template operations, with strict bulkiness/propensity reference lookups, formal-charge/hydrophobic/halogen features, aromatic participant/flag readers, detached chemistry reports, native/table-unit limits and bounded CPU SASA receiving; the
  [receiving record](pending_proposals/molsysmt_tools_addon_receiving.md) names
  exact scope and tests. The backend remains required and legacy addon routes
  remain refused. Python remains the primary headless foundation.
  General automatic edit observation is no longer required; the consumer
  request in uibcdf/molsysmt#413 is withdrawn and closed.
  [Explicit reconciliation/tool coordination](linked_molecular_edits_design.md)
  needs operation-level qualification, deferred-update safety and optional
  recovery contracts. [#262](archive/replacement_load_retains_scene_history.md)
  is fixed independently; the pre-existing box-fixture issue is #263.
  The withdrawn native-Studio expansion plan has been removed at the
  maintainer's request. The new [MolSysMT tools add-on plan](molsysmt_tools_addon_plan.md)
  records accepted requirements: broad expert module/function mirroring,
  implicit current `view.molsys`, thin scientific wrappers and independent
  task-oriented GUI design. Native mutation/return semantics are preserved;
  admitted bound edits synchronize by default and independent results require
  explicit adoption. [Technical receiving](molsysmt_addon_receiving_contract.md)
  is now tracked in uibcdf/molsysviewer#264 and uibcdf/molsysmt#421. The provider
  original source ledger accounts for 267 tracked exports, including
  aliases/support. A 2026-10-23 name-only refresh finds 271; the four new paths
  remain pending adaptation. Broader effect review and qualification remain
  pending. Implementation is owned by the provider repository and undertaken
  by this development effort.
  The [source inventory](studio_molsysmt_operation_inventory.md),
  [operation/recovery proposal](studio_molecular_operations_design.md) and
  [six acceptance scenarios](studio_foundation_workflow_contracts.md) remain
  design inputs. Earlier native-Studio layouts in the
  [prototype review](studio_task_design_review.md) need reassessment; their
  existing evidence does not qualify the new layout. The new tools entry point,
  per-view binding and factory diagnostics have initial source receiving;
  broader edits/namespaces, panels, public package compatibility, freeze and
  publication remain pending. No scientific API is removed.
  Validation: 273 offline link/reporting checks pass, the documentation builds,
  all 174 fixed-source inventory hashes match, and original prototype hashes
  remain unchanged. These checks do not qualify new runtime behavior.

- **Before-documentation cleanup completed — 2026-10-22:** #256 and #260 are
  resolved with local guards, three actual ordinary-cancellation probes and
  current-matrix watermark receiving. The single full local core passes 3,224
  cases; [receiving](pre_documentation_cleanup_20261022.json) keeps operational
  and prior scientific source scopes separate. #261 repairs the final board
  verifier's truncated inventory; complete live reconciliation passes. Both
  handoff anchors are current.
  [#259](pending_proposals/native_copy_contract_receiving.md) remains scoped
  provider receiving; #93 waits for immutable policy/caller/badge adoption.
  These gates cover the existing baseline. The former Studio expansion plan
  is withdrawn; new add-on scope needs its own review. No candidate freeze or publication.

- **Routine Python 3.14 migration completed — 2026-10-21:** source `308ce8fb` passes all eight Linux/macOS 3.11–3.14 cells, the three-host 3.14 source pair and both 44/44 core-browser lanes. API resolution and JS unit/coverage (332/332 in each invocation) execute on Linux 3.14. [Receiving](routine_python314_migration_20261021.json) preserves the local 3,163-pass run, both public recipe dry runs, Sphinx and notebook provenance. The prior routine 3.13 transition is complete. #93 remains partial only for the central immutable admission snapshot and its caller/badge adoption. Qt retains two experimental live failures and ten passing offscreen probes; no freeze or publication.

- **PHMT manual smoke completed / #93 reconciled — 2026-10-21:** Diego confirms all six popup steps as well as Render/Clear and caller-sphere preservation. [Human receiving](pharmacophore_manual_receiving_20261021.json) completes sections 1–3 after the passing 90ebad6d CI; #257 remains resolved. [#93 reconciliation](python314_reconciliation_20261021.json) confirms core Python 3.14 admission and keeps the issue partial for the explicit routine 3.13 recipe/job transition and the central immutable policy delivery. Published policy 1.5.9 and the current 1.5.7 caller still freeze `authorized`; no caller/badge or science change is made from moving central main. No candidate freeze or publication.

- **Human shape-only receiving completed — 2026-10-21:** Diego confirms actual PHMT/Jupyter Render shows both pharmacophore sites and Clear removes them while preserving the independent sphere. [#257 is resolved](archive/shape_only_geometry_not_visible.md), with [human receiving](pharmacophore_manual_receiving_20261021.json) complementing the completed 90ebad6d source CI. Confirmation of the manual independent-window section is requested separately; automated popup guards retain their scope. Finish that manual receiving before reconciling #93. No candidate freeze or publication.

- **Canonical modes / exact-source CI completed — 2026-10-21:** source `90ebad6d` passes all required gates in the [new receipt](canonical_modes_source_ci_20261021.json): six Python 3.11–3.13 cells, all three Python 3.14 hosts, 44/44 core browser suites in both browser lanes, JS unit/coverage 332/332 and notebooks 25/25 in both notebook lanes. The Python 3.14 source pair retains fixed MolSysMT 0.23.0 / `46ef28eb`. Qt remains experimental: two live bridge/WebGL failures and ten passing offscreen probes. Next, resume the actual PHMT/Jupyter visual smoke for [#257](archive/shape_only_geometry_not_visible.md), then reconcile #93; the immutable policy/caller/badge update remains separate. Save outputs, reload the notebook page and restart the 3.14 kernel for manual receiving. No candidate freeze, artifact qualification or publication.

- **Shape-only receiving and canonical modes — 2026-10-21:** the PHMT/Jupyter smoke exposed [#257](archive/shape_only_geometry_not_visible.md): native shape-only geometry existed but the initial camera never framed it. The source correction now commits geometry and requests the first reset without waiting on cached zero Mol* bounds; deliberate viewpoints remain preserved. Actual PHMT Python Render/Clear passes; human browser retest remains pending. Under [#258](archive/retire_classic_canvas_controls.md), Classic is retired and Diego approves `viewer_mode=standard|cinema` and `controls_mode=compact|cinema`, with legacy UI normalization and independent panel-layout names retained. [Receiving](shape_only_controls_validation_20261021.json) separates local checks, prior source CI and new hosted/manual qualification. Finish this retest before #93; no candidate freeze or publication.

- [Final-source CI — 2026-10-21](final_source_ci_20261021.json): accepted source d126c5a1 passes six Python 3.11–3.13 cells, all three Python 3.14 hosts, core browser 44/44, JS unit/coverage 330/330, notebooks 25/25, policy and Conda governance. Qt separately retains two bridge/WebGL failures and ten passing offscreen checks. Next, resume the real PHMT/Jupyter smoke, then reconcile #93 with central admission; the new immutable policy reference is still awaited for caller/badge refresh. [#256](archive/ci_jobs_ignore_cancellation.md) tracks a newly reproduced workflow-cancellation defect; superseded runs were cancelled without touching final receiving. Candidate freeze and publication remain unauthorized.

- [Before-documentation review — 2026-10-21](pre_documentation_review_20261021.json): the initial 29-issue audit identifies no new notebook-core defect. Its queued CI snapshot is superseded by the final-source receipt above. Opacity 98/90/80 is human-accepted; broad documentation follows the requested CI → manual PHMT/Jupyter → #93 sequence.

- **Earlier phase — 2026-10-20: TcTIM / 1TCD pre-1.0 dogfooding with Diego and Liliana.** [Welcome #247 is confirmed resolved](archive/initial_welcome_human_retest.md) by human retest, complementing the guarded source fix and actual-Jupyter receiving. Earlier persistence remains unexplained despite kernel restart/cache reload. [The receipt](initial_welcome_validation_20261020.json) preserves evidence scopes; #248 stays resolved. No candidate freeze or publication is authorized. [Studio handoff #250](archive/studio_remains_in_canvas_popup_after_popout.md) now hides/restores the source panel while preserving notebook layout; [receiving scopes](studio_panel_handoff_validation_20261020.json) remain explicit. Studio now starts unlocked (#252) and its independent popup offers fullscreen (#253); [#251](archive/canvas_popup_blinking_text_caret.md) is now human-confirmed: the cursor has disappeared. Diego confirms the larger #255 card and retains whole-card transparency under #254, accepting three levels 0.98/0.90/0.80, with 0.98 initially. [The restoration receipt](studio_opacity_restoration_20261021.json) records this follow-up; [the preceding source receiving](studio_card_validation_20261021.json) retains its original scope.

- [Latest support receiving — CI follow-up closed](support_library_receiving_20261014.json): SMonitor 0.21.0 build 2 is verified in development; 191 consumer checks pass with 14 intentional skips. Exact 85d30478 hosted scientific 6/6, core browser 43/43, JS unit/coverage, policy and Conda governance pass. Qt retains two bridge/WebGL failures; later scheduled successes only checked backlog and skipped testing. Broad public documentation is next; manual PHMT/Jupyter remains postponed, 0.25.0 unfrozen and both 1.0 publications paused.

- [Latest source hardening](addon_discovery_dependency_validation_20261013.json): #233/#242/#246 fixes pass focused guards, the clean locked npm graph has zero advisories with Mol* 5.4.1 preserved, and published SMonitor 0.20.0 / DepDigest 0.15.1 are received in development. The full local Python run retains three clear-related failures; 27 final affected checks and the final popup guard pass after correction. Browser core passes 43/43 before that final Python correction. Exact 4d15a410 required hosted source qualification passes six Python cells, all three Python 3.14 hosts, core 43/43 and notebooks 25/25; Qt fails in its separate experimental lane; manual Jupyter and publication remain paused.

- [Open-issue reconciliation](open_issue_reconciliation_20261013.md): all 33 initially open issues reviewed; after #245/#239/#233/#242/#246 closures, 29 open issues match 29 local records. #233/#242 have since been corrected; final receiving is tracked above. Exact 19d92c25 required hosted core passes six Python cells, all three Python 3.14 hosts and 43/43 browser suites; [the receipt](addon_window_lifecycle_validation_20261013.json) retains intermediate/final source distinctions and the separate experimental Qt failure. The prepared PHMT/Jupyter smoke is postponed at the maintainer's request.

- [Canvas scientific mirror](canvas_popup_contract.md): #234–#238/#241/#243 implement bidirectional scene receiving, portable native picks and single motion/playback clocks; [evidence](canvas_popup_mirror_validation_20261013.json) preserves all 43 core suites across retained runs/followups, 458 offline guards and the separate source CI/publication scope. Exact 9616b22c hosted browser passes 43/43, including the expanded guard; [#244](archive/scientific_popup_guard_budget.md) closes its scoped budget correction. Dated source/Qt receiving stays in its receipt.
- [Shape-only workspace availability](archive/shape_only_canvas_workspace.md): #240 now opens Studio/Add-ons without atoms and keeps Welcome only for an empty, closed canvas. Real Render/Clear/remount and ownership guard both popups; [regression receiving](shape_only_canvas_workspace_validation_20261013.json) stays separate from installed qualification.

- [Canvas popup parity](canvas_popup_contract.md): #232 aligns runtime, controls, preferences, keyboard and popup actions; its [closure](archive/canvas_popup_controls_parity.md) retains real widget/export guards and passing core 43/43; [source CI receiving](canvas_popup_validation_20261013.json) tracks the integrated 63c3d9c7 separately.

- [Core/Qt qualification scope](core_qt_qualification.md): #231 separates required core from native experimental diagnostics, retaining independent official outcomes and recovery watermarks.
- [Gate receiving receipt](core_qt_qualification_20261013.json): prior exact source has scientific 6/6, Python 3.14 hosts 3/3, core 43/43 and notebooks 25/25; the new wiring passes the full local core (3,095 passed, 21 skips), with its own source evidence.

- [Integrated scientific/resource review](integrated_review_20261010.md): #200 records local ownership and #228–#230 correct export/fixture/preview lifecycle; 137 science checks and 43/43 core suites pass; its exact hosted source review is complete, with Qt failure retained.
- [Temporary resource lifecycle](temporary_resource_lifecycle.md): applicable owners, managed cleanup, retained evidence and bounded Qt/forced-termination exceptions.

- [Studio coverage review](studio_coverage_20261010.md): #223–#225/#227 complete focus, visibility, work files, figure persistence and examples; #226 defers Copy Python.

The next agreed version is [0.25.0](stabilization_025_preparation_20261009.md);
further changes remain, so its producer and staging qualification are not frozen.
Both 1.0 publications remain paused.

- [Public Python API review](public_api_review_20261010.md): the final source round covers #210–#216 and optional handle parity #217; exact candidate and installed qualification remain separate.
- [Public API follow-up](public_api_followup_20261010.md): #218–#222 close query scope, retired reads, mode history, handle annotations and visual-state ownership before freezing a candidate.

- [Studio integration review](studio_review_20261009.md): both authorized rounds (#181–#188 and #190–#197/#199) implement native ownership, export/geometry, persistent editors, search/batches and disclosures; source/browser evidence retains Qt limits and the resolved #189/#198 follow-ups.
- [`canvas_context_menu_pre_1_0_plan.md`](canvas_context_menu_pre_1_0_plan.md): #179's contextual workflows, picking corrections and parallel menus are accepted in the notebook; Cinema and consistent controls reveal are tracked under #180. Publication remains paused and 0.24.1 needs a replacement candidate.
- [`open_issue_reconciliation_20261007.md`](open_issue_reconciliation_20261007.md): complete 34-issue scope review, public-promise corrections, historical publication decisions and remaining 1.0 gates.
- [`public_distribution_contract.md`](public_distribution_contract.md): public Conda/core backend route and experimental native-host boundary.
- [`interactions_compatibility_contract.md`](interactions_compatibility_contract.md): agreed experimental consumption, identity, paging, geometry and invalidation limits for the next installed pair.
- [`stabilization_0241_preparation_20261008.md`](stabilization_0241_preparation_20261008.md) and [receipt](stabilization_0241_preparation_20261008.json): preserved build-1 files and prerequisites; provider reports installed 16/16 success, independent Viewer archive review is incomplete and paused, and this candidate will be superseded by the menu work.
- [`stabilization_0241_provider_source_review_20261008.json`](stabilization_0241_provider_source_review_20261008.json): independent hashes and inspection of all eight provider scientific certificates and full-suite JUnit ZIPs; source 8/8 passes, with skips preserved.

- [`human_usability_review_20261006.md`](human_usability_review_20261006.md): completed five-stage remote-Jupyter review with Diego; observations, corrected usability defects and tutorial follow-up retained.

- [`scientific_usability_review_20261004.md`](scientific_usability_review_20261004.md): real widget findings, separate Interactions calculation/display scopes and successful repaired-provider SDF composition.

- [`scientific_use_review_20261004.md`](scientific_use_review_20261004.md): real
  molecular workflows, reproduced SDF/hierarchy gaps and their owning issues.
- [`integration_review_20261003.md`](integration_review_20261003.md): reviewed
  source integration, validation limits and deferred CI evidence.
- [`version_assessment_20261003.md`](version_assessment_20261003.md): proposed
  minor version and the remaining gates before a new tag.
- [`checkpoints.md`](checkpoints.md): current repository handoff.
- [`reporting_protocol.md`](reporting_protocol.md): **normative.** How a defect or a
  proposal enters `pending_bugs/` and `pending_proposals/`, how those stay in step with
  the GitHub issue board, and what closing one requires. Read it before adding a document
  to either queue; start from [`templates/report.md`](templates/report.md).
- [`capability_audit.md`](capability_audit.md): one row per capability — public API,
  provenance, documentation, tests, status and the release it first shipped in.
  **Generated**; regenerate with `python devtools/capability_audit.py --write`. Read it
  before writing any claim about what MolSysViewer does.
- [`path_to_1_0.md`](path_to_1_0.md): release gate toward `1.0.0`.
- [`release_gate_evidence.md`](release_gate_evidence.md): local exact-candidate
  staging/public/hosted evidence checks and bounded pre-1.0 exception reporting.
- [`dependency_contract.md`](dependency_contract.md): canonical requirements,
  secondary packaging/environment routes and installed source-provider checks.
- [`roadmap.md`](roadmap.md): current execution priorities.
- [`interactions_pre_1_0_plan.md`](interactions_pre_1_0_plan.md): approved
  delivered bounded Interactions sequence; archived #114/#140 and workflow
  records #142/#144/#145 retain the public-pair qualification and guards.
  Final 1.0 recertification remains in the release plan.
- [`interactions_performance.md`](interactions_performance.md): measured combined
  coordinate/analysis residency, real detector timing and sparse queries;
  public-pair qualification is complete; native-GPU throughput and arbitrary
  large-system limits remain uncertified.
- [`interactions_qualification.md`](interactions_qualification.md): real scientific
  query/geometry, H5MSM/session and calculated-link browser evidence, with the
  explicit published-provider boundary.
- [`installed_artifact_qualification.md`](installed_artifact_qualification.md):
  fixed Viewer 0.24.0 build 1 / MolSysMT 0.23.0 ABI3 build 0 qualified in all
  sixteen staging and public cells, exact Windows launchers and hosted core browser
  suites; the final 1.0 candidate and later source corrections retain separate gates.
- [`stabilization_024_preparation_20261006.json`](stabilization_024_preparation_20261006.json):
  exact candidate coordinates, artifact digests, native CI verdicts and publication boundary.
- [`pending_bugs/`](pending_bugs/): confirmed unresolved defects.
- [`pending_proposals/`](pending_proposals/): active proposals, with its own
  indexed status table.
- [`pending_proposals/post_1.0/`](pending_proposals/post_1.0/): explicitly
  deferred work, including remote-session support and E2E certification
  (`uibcdf/molsysviewer#100`).

An implemented design does not remain under `pending_proposals/`. Implementation
plans are removed once their durable contracts and public documentation exist;
Git retains the plan.

## Durable engineering references

### Runtime and protocol

- [`data_plane_architecture.md`](data_plane_architecture.md) — how structural
  arrays travel as typed binary buffers, planar per structure. **Complete for
  pre-1.0** (D0–D4 and the Qt payload scheme).
- [`runtime_message_router.md`](runtime_message_router.md) — envelopes, identity,
  authority and the shared action manifest. **Complete for pre-1.0** (R0–R4).
  `checkpoints.md` sends every new session to these two first.
- [`architecture.md`](architecture.md)
- [`units_and_quantities.md`](units_and_quantities.md)
- [`js_runtime_build_and_version_sync.md`](js_runtime_build_and_version_sync.md)
- [`load_modes_and_append_structures_status.md`](load_modes_and_append_structures_status.md)
- [`python_js_boundary_audit_2026_07.md`](audits/python_js_boundary_audit_2026_07.md)
- [`python_ecosystem_policy_adoption.md`](python_ecosystem_policy_adoption.md): independent support/tooling review states and their evidence.
- [`pytest_receptor.md`](pytest_receptor.md)
- [`smonitor.md`](smonitor.md)

### Interaction and scene semantics

- [`interaction_overview.md`](interaction_overview.md)
- [`interaction_targets_and_selection.md`](interaction_targets_and_selection.md)
- [`interaction_gestures_and_menus.md`](interaction_gestures_and_menus.md)
- [`interaction_modifiers_and_future.md`](interaction_modifiers_and_future.md)
- [`interaction_verified_state.md`](interaction_verified_state.md)
- [`selections.md`](selections.md)
- [`annotations.md`](annotations.md)
- [`strips.md`](strips.md)
- [`molstar_color_strings.md`](molstar_color_strings.md)

### Product surfaces

- [`competitive_positioning.md`](competitive_positioning.md) — what the project
  competes on, what it concedes, and which concession is structural. Includes
  the agent-facing reading of the reproducibility thesis, and the two distinct
  design targets it implies — the agent operating the viewer, and the assisted
  human operating it.
- [`canvas_minimal_ux.md`](canvas_minimal_ux.md)
- [`image_export_direction.md`](image_export_direction.md)
- [`addon_panel_widget_contract.md`](addon_panel_widget_contract.md)
- [`molsyssuite_addon_direction.md`](molsyssuite_addon_direction.md)
- [`smoke_test.md`](smoke_test.md)
- [`benchmarks/README.md`](benchmarks/README.md)

### Performance baselines

Measured evidence, not estimates. Each records the command that reproduces it.

- [`performance/trajectory_transport_baseline_2026_07.md`](performance/trajectory_transport_baseline_2026_07.md)
  — AnyWidget trajectory transport.
- [`performance/qt_transport_baseline_2026_07.md`](performance/qt_transport_baseline_2026_07.md)
  — Qt standalone transport; why binary needs no new channel.
- [`performance/message_path_regression_check_2026_07.md`](performance/message_path_regression_check_2026_07.md)
  — the post-envelope message-path baseline required by
  [`engineering_rules.md`](engineering_rules.md) §6.
- [`performance/startup_baseline_2026_07.md`](performance/startup_baseline_2026_07.md)
  — what a first canvas actually costs, split into one-time, per-viewer and
  per-load. Replaces the retired Numba JIT figures.

### Standalone

- [`standalone_direction.md`](standalone_direction.md) — **the decision, and the
  one to read first: one workbench model, multiple hosts.** Standalone is not a
  second product with its own interaction model or scene architecture.
- [`standalone_host_plan.md`](standalone_host_plan.md) — that direction turned
  into the operational pre-1.0 plan.
- [`standalone_supported_environment.md`](standalone_supported_environment.md) —
  the supported development-time environment recipe.
- [`standalone_packaging_strategy.md`](standalone_packaging_strategy.md) — how
  the host is packaged and distributed.
- [`standalone_qt_ci_and_gl_decisions.md`](standalone_qt_ci_and_gl_decisions.md)
  — CI and GL decisions closed on 2026-07-04 against a real GPU. **Not to be
  re-litigated without a new reason.** Spanish.
- *(`standalone_performance_and_depythonization.md` was archived on 2026-08-06:
  it argues from Numba JIT cold-start latency, and MolSysMT no longer uses
  Numba.)*
- [`standalone_v2_evolution_plan.md`](standalone_v2_evolution_plan.md) — post-1.0
  architecture for a v2 host, beyond the monolithic PySide6 prototype.

The [2026-10-29 standalone review](standalone_review_20261029.md) repairs live
Qt authority/preferences, profile ownership, native downloads and movie/image
export. Native Linux/GPU guards pass; #35 still needs maintainer visual
confirmation. #109/#113 retain platform/resource qualification, and #51 keeps
Qt popout work separate. Qt remains experimental. Older investigations live
under [`audits/`](audits/README.md).

## Project direction

These documents explain product intent, not current implementation status.
Read them in this order: the first two say what the product *is*, the next three
scope 1.0, and the last four describe work that begins after it.

1. [`guiding_principles.md`](guiding_principles.md) — the ideas-alma: what the
   product is for, and what it refuses to become.
2. [`development_mantra.md`](development_mantra.md) — the practical conclusions
   that stay visible while writing code.
3. [`v1_vision_and_styles.md`](v1_vision_and_styles.md) — the 1.0 scope: half
   visualiser, half instrument, and what that costs.
4. [`scene_look_styles_direction.md`](scene_look_styles_direction.md) — the next
   careful step after the first scene-style slice.
5. [`style_battery_and_future_ideas.md`](style_battery_and_future_ideas.md) —
   which styles ship first, so style growth stays intentional.
6. [`molsysmovie_vision.md`](molsysmovie_vision.md) — post-1.0: a separate
   `MolSysMovie` surface for timelines and keyframes, kept out of the viewer.
7. [`render_quality_vision.md`](render_quality_vision.md) — post-1.0: **the
   project does intend to compete with desktop-quality rendering**, by bridging
   to Blender rather than replacing Mol\*.
8. [`future_vision_beyond_1_0.md`](future_vision_beyond_1_0.md) — post-1.0
   frontier ideas, including live streaming from a running simulation. Spanish.
9. [`areas_of_opportunity_analysis.md`](areas_of_opportunity_analysis.md) —
   five opportunity areas with feasibility analysis. Spanish. **Its "Estado
   Final de Implementación" sections record intent at the time of writing and
   have been contradicted by the code since; `scene_contracts.md` wins.**

## Course material

Course planning is isolated under [`course/`](course/):

- [`course/introduction.md`](course/introduction.md)
- [`course/common_core.md`](course/common_core.md)
- [`course/structure.md`](course/structure.md)

Course plans are not API references. Every example must still be checked against
the current public API before execution.

## Historical implementation records

[`archive/`](archive/README.md) contains completed implementation plans retained
only when their rationale remains useful. They are not current instructions.
Closed audits are stored separately in [`audits/`](audits/README.md).

## Maintenance rules

- Do not append historical sessions to `checkpoints.md`.
- Do not copy normative clauses into plans; link to the contract.
- Every proposal declares one of: `proposed`, `approved`, `blocked`,
  `post-1.0`, or `implemented`.
- `implemented` documents are promoted to a durable reference or removed from
  `pending_proposals/`.
- Performance claims without a reproducible benchmark are labeled estimates.
- A document naming current code or APIs must be checked against the repository,
  not against an earlier plan. A contract or a procedure that names something the
  code does not have is making a false claim, not a plan — that belongs in a
  proposal, where naming what you intend to build is the point.

### Say "done" where a scan will hit it

Documents are read by skimming, so **a closed item is only closed if that is
visible at scan depth**. Three rules follow, and this round is the evidence for
all three — a handoff rewritten in the morning still listed as open the three
things finished that afternoon, and an inventory of nineteen items had seven
bodies contradicting their own headers.

1. **The state goes in the title**, or in the first line of the file. Never only
   in the body: a reader who skims a long body concludes the work is pending, and
   the longer the body, the likelier that is.
2. **Text in place is inversely proportional to how closed something is.** A
   closed item keeps one line — the outcome and where the evidence lives. Its
   reasoning goes to `archive/`, or stays in the git history. Preserving a
   finished item's full *What / Why / How* beside the open ones is what makes an
   inventory read as a work queue.
3. **When you finish something, close it in its home document in the same
   change.** Not in a summary, not in a commit message: in the file the next
   reader will open.

### Prose for prose, lists for lists

28 % of the lines in this directory are bullets, and most of the excess comes
from one habit: a lead-in ending in a colon — `Reason:`, `Preferred direction:`
— followed by three or four bullets that carry one idea each. That is a sentence
written as a diagram. It reads slower, not faster, and it triples the length of
what a skim has to cross before reaching the point.

- **A list earns itself when its items are enumerable and independent** — the
  clauses of a contract, colour names, the steps of a procedure, a table of
  measurements. `scene_contracts.md` is rightly full of them.
- **Otherwise write the sentence.** "Minimal, elegant and low-noise, consistent
  in stroke and weight" says exactly what five bullets said, in one line.
- **Drop the orphan lead-in.** If a colon introduces reasoning rather than
  items, the reasoning is the sentence.

Rewriting one section of `canvas_minimal_ux.md` this way took it from 45 lines
to 19 and from 184 words to 127, with every claim intact. The line count falls
faster than the word count, which is the honest description: this is about
layout, not about cutting content. **Nothing may be lost — if a rewrite drops a
claim, it is a different document, not a shorter one.**
