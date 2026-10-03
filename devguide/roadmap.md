# Development roadmap

**Updated:** 2026-10-03

This roadmap states current priorities. Release gating lives in
[`path_to_1_0.md`](path_to_1_0.md), normative behavior in
[`scene_contracts.md`](scene_contracts.md), and concrete open designs in
[`pending_proposals/`](pending_proposals/).

## Current execution order — 2026-10-03

The accumulated Interactions, composite loading, public API and scene corrections
are reviewed and integrated in `main` at `0dea171d`. The latest complete source
regression passes **2,805 tests, 23 skipped** in the required Python 3.14
development environment. The integration review also corrected repeated-frame
display transfer (#156). Ruff, TypeScript and runtime rebuild pass. Prior local
core-browser evidence is **39/39** under the normal deadline; installed evidence
retains its original artifact boundaries. See [the handoff](checkpoints.md).

CI enforcement (#116), ecosystem adoption (#110), scalar units (#98), diagnostics
(#107) and dependency contracts (#106) are resolved. PR #135 merged after
updated-commit hosted checks; its results remain tied to that commit. Work with
the principal maintainer uses reviewed commits and direct pushes, without PRs.
This source integration uses the existing internal deferred CI route: ordinary
CI still selects public MolSysMT 0.22.4, which lacks Interactions. No exact
hosted-candidate pass is claimed.

Next reconcile devguide, assess a new minor version and review representative
scientific use. Then qualify Interactions with a compatible published provider
(#114/#140), repaired exact Conda/Windows artifacts (#101), the current 16-cell
installed pair and hosted core browser requirements. Public documentation
follows functional closure. Finally freeze the release candidate and retain
scientific dogfooding, first-contact and exact-artifact evidence. Historical
outcomes remain in their dated records; see
[the integration review](integration_review_20261003.md).

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
   `uibcdf/molsysviewer#114`. Complete MolSysMT addon retirement and Mol* dependency
   upgrade are outside this gate.

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
