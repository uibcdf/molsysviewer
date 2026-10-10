# Development roadmap

**Current execution order — 2026-10-10:** the
[canvas context-menu redesign](canvas_context_menu_pre_1_0_plan.md) (#179/#180)
is accepted. The authorized Studio round (#181–#188), including removal
of the MolSysMT addon, is implemented. The second Studio round (#190–#197,
#199) implements Shapes geometry/feedback, executable guides, persistent editors,
named controls, local search, marked batches and disclosures. The final review
(#201–#204) closes creation failure recovery, atomic initial layer membership,
new-region draft persistence, annotation coordinates and confirmed analysis deletion. Review its
[source/browser evidence](studio_review_20261009.md), live notebook and hosted
results; reconcile the macOS dynamic-region diagnosis (#189) and the historical
source-pair PNG timeout (#198, partial).
Then prepare and qualify the agreed 0.25.0 candidate, complete public documentation
and installed first contact, and independently qualify the eventual 1.0 producer.
Viewer/MolSysMT 1.0 publication is paused by the maintainer. Keep the
[0.24.1 build-1 preparation](stabilization_0241_preparation_20261008.md) and its
exact files/evidence fixed; they do not qualify the changed menu. The next
version is agreed, but its producer/build qualification is not frozen.
Public packages remain 0.24.0/0.23.0 and the
[experimental Interactions contract](interactions_compatibility_contract.md)
remains unchanged.

**Complete board review — 2026-10-07:** [all 34 open issues are reconciled](open_issue_reconciliation_20261007.md).
#95/#97 public installation/host promises are corrected; #78 retains developer-only
quarantine and #152's original guide publication is complete. The maintainer
closes #82/#89 as superseded by verified 0.24.0, without historical backfill.
#93 still needs central Python admission despite delivered public 16/16 evidence.
#42's published detection repair removes its historical loading bottleneck; the
explicit source hint remains a non-gating provider improvement. Remaining 1.0
work includes public docs/installed first contact, Interactions compatibility
freeze and exact artifact/gates containing the source-only #149/#177 fixes.
Experimental Qt defects and post-1.0 growth are not a core release clearance.


**Updated:** 2026-10-09

This roadmap states current priorities. Release gating lives in
[`path_to_1_0.md`](path_to_1_0.md), normative behavior in
[`scene_contracts.md`](scene_contracts.md), and concrete open designs in
[`pending_proposals/`](pending_proposals/).

## Delivered stabilization baseline — 2026-10-07

The fixed stabilization package is Viewer **0.24.0 noarch build 1** from
`1a4c97a58b68b69f3a836546c9e4ac6187c3efa2`, paired with MolSysMT **0.23.0 ABI3
build 0** from `46ef28eb60a258aa77d82ff1bc39ee0d1591e3c9`. All **16/16** installed
staging cells, exact Windows launchers and **39/39** hosted core suites pass;
independent reads verify the actual installed artifact inventories and hashes.
All six Linux/macOS Python 3.11–3.13 regression cells pass. The separate Qt job
still fails on its known experimental WebGL path (#109). Canonical-source
Python 3.14 integration passes on all three native hosts, with 39 core suites
and all 25 notebooks passing on Linux.
The provider's final-source gate also passes all eight Linux/macOS Python
3.11–3.14 cells with the exact Viewer commit: 54/54 scientific cases per cell
without omissions, and 13,323 full-suite cases per cell with zero failures/errors.
Independent certificate/JUnit downloads preserve the optional/environment skips.
See [the current handoff](checkpoints.md#resume-in-one-page) and
[the preparation receipt](stabilization_024_preparation_20261006.json).

The cumulative scene/API, Interactions, mixed-source loading and support-library
changes are integrated. The five-stage human review is complete. Temporary-tag,
Movie completion, automatic-source version and hosted-control evidence defects
(#171–#175) are resolved; developer-tooling successors do not replace the frozen
package producer. Earlier failed attempts retain their original verdicts.

The corrected automatic-development hosted follow-up passes on all three native
hosts, including 39 core suites and 25 notebooks on Linux. Devguide reconciliation
and its issue-board checks pass. Both owners confirm the fixed candidates and
MolSysMT-first / Viewer-second publication sequence. MolSysMT 0.23.0 is now
published: its exact tag and four original ABI3 build-0 files, public labels
and solver indices are independently verified. Its source preservation is now
verified at version DOI [10.5281/zenodo.23205366](https://doi.org/10.5281/zenodo.23205366),
with matching receipt and public API inventory. Diego authorizes Viewer publication
on 2026-10-07, and the exact canonical 0.24.0 tag is pushed. Its npm publisher
initially fails on an already synchronized manifest (#176). Recovery run
`37586395370` and independent npm/CDN integrity/version checks pass. Viewer
Release is published, Conda build 1 is promoted unchanged and public labels/index
are verified; build 0 remains staging-only. Viewer source preservation is
verified at [10.5281/zenodo.23206053](https://doi.org/10.5281/zenodo.23206053).
All **16/16 public installed cells** pass in
[37587631519](https://github.com/uibcdf/molsysmt/actions/runs/37587631519).
All actual environment ZIPs/digests, exact public package coordinates and four
required steps per cell are independently verified. The exact-source
`public_conda` gate also passes. Coordinated stabilization publication is complete.
Supported-provider records #114/#140/#151 are resolved with that evidence,
the updated Interactions guide and 207 fresh installed scientific/loading checks.
Workflow follow-ups #142/#144/#145 are resolved with 47 fresh installed tests and
five executable guide blocks for paging, scientific files and participant actions.
Design corrections #146/#147/#148 are resolved with 27 fresh installed checks,
twelve labels-guide blocks and conservative legacy fingerprint recovery.
Movie interruption #177 is corrected in source `7880e2e3`: stop restores the
observed camera and awaits its fresh draw even after command promises resolve.
Core `37680239149` passes 39/39; exact-source pair `37680239068` passes all three
Python 3.14 hosts, plus 39 core suites and 25 notebooks on Linux. Earlier Movie
failure verdicts remain preserved in [the correction receipt](movie_interruption_fix_20261007.json).
Standard CI `37680239319` passes six scientific cells but retains its experimental
Qt WebGL startup failure (#35). The source correction does not replace published
0.24.0 artifacts or qualify the eventual 1.0 candidate.
#149/#150 are resolved with [the styles/plot closure](styles_plot_closure_20261007.json).
Numeric plot sources/guards match the public producer, with twelve fresh installed
checks and seven geometry/seeking units passing. The remaining applied-recipe
alias found in the public package is corrected in source `027374ed`; its reviewed
checkpoint `bd824ea1` passes thirteen installed development-wheel guards,
three-host Python 3.14 source pair `37685753081`, 39 core suites and 25 notebooks.
The correction awaits the next qualified release; public 0.24.0 files are unchanged.
#143 multi-card lifecycle is also resolved with six fresh installed guards and
two executable guide examples on the original promoted public-version files;
[the closure record](trajectory_plot_lifecycle_closure_20261007.json) binds the
unchanged owners to existing hosted/browser evidence.
#101/#153/#154/#155 are resolved: the separate exact-file public Windows
launcher gate passes, alongside 49 installed CLI/worker/box checks and twelve
launcher/runner guards. [The closure record](remaining_partial_closure_20261007.json)
preserves artifact digests, unchanged owners and historical failures.
Next reconcile broader documentation and complete installed first-contact observations
and the final 1.0 candidate decision as distinct remaining work. Standalone remains
experimental; remotes and the Mol* dependency update remain post-1.0.

## Pre-1.0 distribution milestone completed — 2026-09-25

Viewer 0.23.4 and MolSysMT 0.22.4 are published as a compatible pair. The
exact public Conda pair passed 20/20 clean installations on five platforms
and Python 3.11–3.14; the Viewer npm runtime and matching CDN bundle are
also public. The hard-dependency channel cycle is no longer the next
roadmap blocker. See [the current checkpoint](checkpoints.md) for exact
evidence and the release issues.

This milestone certifies core package installation, not every optional Qt
host or scientific workflow. The 34-case core E2E passed on hosted Chrome
at exact commit `6b519db0` in
[run 36232475620](https://github.com/uibcdf/molsysviewer/actions/runs/36232475620);
visible-window Qt remains unverified. The local standalone host and launchers
remain experimental in 1.0, so those observations are outside the strict
release gate. The remote-session feature and its three E2E scenarios are
post-1.0 preview work (`uibcdf/molsysviewer#100`). The strict 1.0 gate remains
open. Both Zenodo exact-version records are now published and independently
verified. The execution order above governs the current session; representative
scientific dogfooding, first-contact onboarding and exact-candidate evidence
remain release requirements. The false-red promotion verifier has been
replaced by a read-only check that passed on GitHub for the published pair;
the earlier promotion jobs remain red (`uibcdf/molsyssuite#48`).

The shared Linux Python 3.14 development environment now uses official
conda-forge PySide6/Qt 6.11.2; the UIBCDF Qt family is kept separately
for rollback (`uibcdf/molsyssuite#52`). This is a development baseline,
not a 1.0 host certification. Comparing newer conda-forge Qt families through
standalone dogfooding (`uibcdf/molsysviewer#113`) is an experimental-host
follow-up, not a condition for freezing the 1.0 candidate. Canonical-host
migration and its remaining platform observations stay in
`uibcdf/molsysviewer#109`.

## Completed foundations

- Reproducible scene state, state v2, replay, export, and one scene history.
- Whole/region representation contracts and exclusive atom ownership.
- Layered color, region order, dynamic region recipes, and rebuild behavior.
- Canonical managers for regions, layers, shapes, annotations, measurements,
  and selections.
- Studio subpanels for all current core domains plus Viewport and Export.
- Add-on workspaces and panel widgets.
- Figure, HTML, image, and movie export foundations.
- Persistent clipping sections and creator attribution.
- Public-unit consistency through PyUnitWizard.
- Python/TypeScript protocol and argument-digestion guards.
- Standalone Qt host-side error handling and bounded delivery retries.

## Pre-1.0 gates

These are the release gates:

1. ✅ **Closed 2026-07-30.** Array-native transport for all structures selected
   into `view.molsys`: no intermediate-form/nested-list/text-JSON coordinate path when
   binary is negotiated; behaviorally equivalent JSON fallback; representative
   atom-count and structure-count measurements. Qt serves raw arrays through the
   `molsysviewer-payload` scheme handler it already had. Evidence in
   [`performance/`](performance/); per-gate detail in `path_to_1_0.md`.
2. ✅ **Closed 2026-07-30.** One typed runtime router across Python, widget/Qt
   hosts, embedded canvases, and popups, with Python as the only reproducible
   mutation authority. `runtime_actions.json` is the shared manifest both ends
   validate against; `WidgetRuntimeRouter` owns identity, direction and command
   deduplication.
3. Scientific dogfooding on representative laboratory workflows.
4. ✅ **Scope decision 2026-09-28.** The local standalone host is experimental
   for 1.0. Real-window Qt/WebGL and live-replacement observations remain open
   for that host, but do not block the core 1.0 release.
5. **Public core-pair distribution completed 2026-09-25; final end-user
   first-contact validation remains.** Dependency-channel synchronization
   is evidenced by the 20-cell public matrix, not by a source checkout.
6. First-contact README/onboarding verification.
7. Documentation and package-version consistency at the release commit.
8. ✅ **Updated 2026-10-03.** All 715 ordinary public callable routes,
   including exported class methods and returned scene handles, have ArgDigest
   and explicit `skip_digestion=False`. There are no exemptions or missing
   named digesters (`uibcdf/molsysviewer#125`). The behavioral and inventory guards are recorded in
   [`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md)
   (Phase 10, gate 9).
9. **Source implementation integrated 2026-10-03; published qualification pending.**
   Interactions covers nine explicit families, grown from the initial hydrogen
   bond/disulfide minimum, with Python API first and a minimal Studio
   subpanel after its contract is settled. Native calculation and declared
   H5MSM import store analyses in `view.molsys.interactions` without addon
   registration. Scientific queries, import, calculation and session persistence
   are implemented, including tagged displays, browser projection and Studio.
   Review corrections and six synthetic joint memory/query measurements are
   recorded. Bounded real scientific and calculated-link browser qualification
   now pass, including a real 5,000-frame calculation; see
   [`interactions_qualification.md`](interactions_qualification.md).
   Published-provider, larger GPU and exact-candidate
   qualification remain pending. The final design review is implemented under `uibcdf/molsysviewer#118`–`#125`; exact-candidate validation remains.
   Public bounded pages are requested in `uibcdf/molsysmt#264`; public-reference
   warnings and cold imports found during Sphinx validation were corrected in
   `uibcdf/molsysviewer#117`; its strict Sphinx and full Python gates pass.
   The Python API design is in the active proposal.
   Coordinate result semantics with
   `uibcdf/molsysmt#250`; follow
   [`interactions_pre_1_0_plan.md`](interactions_pre_1_0_plan.md) and
   `uibcdf/molsysviewer#114`. MolSysMT addon retirement belongs to the Studio round
   (uibcdf/molsysviewer#186). The Mol* dependency upgrade remains post-1.0.

The local standalone launchers and Qt host may remain distributed for
evaluation; they carry no supported 1.0 host contract. Interactive HTML export
remains a supported output format. The remote-session implementation was
demonstrated before 1.0, but its
supported feature contract and E2E certification now belong to post-1.0.
Existing entrypoints may remain in the distribution as an unsupported preview;
their presence does not certify remote rendering, deployment or compatibility.
See [`remote_rendering_plan.md`](remote_rendering_plan.md) and
`uibcdf/molsysviewer#100`.

## Active pre-1.0 execution

The transport and routing contracts landed in gates 1 and 2. The architecture
rework found by the subsequent repository audit and JupyterLab smoke testing is
implemented through Phase 8: typed transfer lifecycle, lazy generation-bound
fallback, canonical static/live projection, endpoint ownership, seam evidence
and representative performance/memory gates. Phase 9 reconciled durable
documentation; Phase 10 owns the remaining product/release gates. The canonical
dashboard is
[`pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md).

The durable contracts record what was built and why:

- [`runtime_message_router.md`](runtime_message_router.md);
- [`data_plane_architecture.md`](data_plane_architecture.md).

The explicit uniform-color API requested during dogfooding is implemented as
`Whole.set_color` and `Region.set_color`. The Qt live-replacement defect has an
implemented automated regression path; repeated visible-window validation
remains manual. Camera snapshot acquisition for movie export is a confirmed
post-1.0 bug.

The 1.0 data work does not change scientific residency: all selected structures
remain materialized in `view.molsys`. Lazy sources and eager/windowed modes are
post-1.0 research.

Startup/message-cost work is closed: message replay is no longer synchronized
per queued message, the public package is lazy, and the relevant ecosystem
overhead was addressed upstream. The server render worker was accepted as a
prototype placement and does not change scientific residency.
Configurable picking, advanced Interactions, multiview, general computation/serialization
worker offload, compression and shared-memory transport remain post-1.0. The
server render worker's prior placement is prototype evidence, not a supported
1.0 remote workflow. See
[`remote_rendering_plan.md`](remote_rendering_plan.md) and
[`pending_proposals/README.md`](pending_proposals/README.md).

## Post-1.0

- Advanced MVS annotation machinery.
- Additional Interactions families, analytics, imports, and advanced Studio UI.
- Mol* dependency update (`uibcdf/molsysviewer#115`).
- Configurable canvas picking level.
- Multi-view/split-screen synchronization.
- Lazy structure sources and partial materialization.
- Large-system rendering tiers that require Mol* upstream work.
- Cross-platform standalone packaging.
- Standalone host certification after experimental use and real-window
  observations.
- Supported remote sessions after portable-client and server-GPU certification.
- Managed TURN, multi-user remote collaboration, GPU worker pools and cluster
  scheduling beyond the single-session remote-rendering contract.
- Advanced rendering and cinematic/VR directions.

## Decision filter

Prefer work that:

- improves a real scientific workflow;
- preserves reproducibility;
- has a measurable bottleneck or verified defect;
- reuses MolSysMT and Mol* rather than duplicating scientific or rendering
  engines;
- keeps Jupyter, export, popup, and standalone behavior aligned.
