# Development roadmap

**Updated:** 2026-09-26

This roadmap states current priorities. Release gating lives in
[`path_to_1_0.md`](path_to_1_0.md), normative behavior in
[`scene_contracts.md`](scene_contracts.md), and concrete open designs in
[`pending_proposals/`](pending_proposals/).

## Pre-1.0 distribution milestone completed — 2026-09-25

Viewer 0.23.4 and MolSysMT 0.22.4 are published as a compatible pair. The
exact public Conda pair passed 20/20 clean installations on five platforms
and Python 3.11–3.14; the Viewer npm runtime and matching CDN bundle are
also public. The hard-dependency channel cycle is no longer the next
roadmap blocker. See [the current checkpoint](checkpoints.md) for exact
evidence and the release issues.

This milestone certifies core package installation, not every optional Qt
host or scientific workflow. Visible-window Qt and hosted core E2E
remain unverified 1.0 gates. The remote-session feature and its three E2E
scenarios are now post-1.0 preview work (`uibcdf/molsysviewer#100`), and the
strict 1.0 release gate remains open. Both Zenodo exact-version records are
now published and independently verified. Next prioritize
the remaining real-window observations, representative scientific
dogfooding, first-contact onboarding, reproducible hosted E2E evidence and
an exact-commit 1.0 candidate. The false-red promotion verifier has been
replaced by a read-only check that passed on GitHub for the published pair;
the earlier promotion jobs remain red (`uibcdf/molsyssuite#48`).

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
4. Real-window Qt/WebGL validation of load, interaction, context menu, and the
   implemented live-replacement regression.
5. **Public core-pair distribution completed 2026-09-25; final end-user
   first-contact validation remains.** Dependency-channel synchronization
   is evidenced by the 20-cell public matrix, not by a source checkout.
6. First-contact README/onboarding verification.
7. Documentation and package-version consistency at the release commit.
8. Close the decided `@digest` policy over the supported public callable
   surface, with argument digesters and catalogued diagnostics rather than
   decoration-only coverage.

The remote-session implementation was demonstrated before 1.0, but its
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
overhead was addressed upstream. The server render worker is now an accepted
pre-1.0 standalone placement and does not change scientific residency.
Configurable picking, Interactions, multiview, general computation/serialization
worker offload, compression and shared-memory transport remain post-1.0. See
[`remote_rendering_plan.md`](remote_rendering_plan.md) and
[`pending_proposals/README.md`](pending_proposals/README.md).

## Post-1.0

- Advanced MVS annotation machinery.
- Interactions domain and Studio subpanel.
- Configurable canvas picking level.
- Multi-view/split-screen synchronization.
- Lazy structure sources and partial materialization.
- Large-system rendering tiers that require Mol* upstream work.
- Cross-platform standalone packaging.
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
