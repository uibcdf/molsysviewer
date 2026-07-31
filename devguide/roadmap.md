# Development roadmap

**Updated:** 2026-07-29

This roadmap states current priorities. Release gating lives in
[`path_to_1_0.md`](path_to_1_0.md), normative behavior in
[`scene_contracts.md`](scene_contracts.md), and concrete open designs in
[`pending_proposals/`](pending_proposals/).

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
   into `view.molsys`: no `ViewerJSON`/nested-list/text-JSON coordinate path when
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
5. End-user installation and dependency-channel synchronization.
6. First-contact README/onboarding verification.
7. Documentation and package-version consistency at the release commit.

## Active implementation candidates

*Obsolete since 2026-07-30*: this section described the transport and routing
foundations as the remaining pre-1.0 architectural work. Both landed (gates 1
and 2 above), so **no architectural work is open for 1.0** — what remains is
verification, dogfooding and release hygiene. The two proposals stay as the
design record of what was built and why, not as pending work:

- [`pending_proposals/runtime_message_router.md`](pending_proposals/runtime_message_router.md);
- [`pending_proposals/data_plane_architecture.md`](pending_proposals/data_plane_architecture.md).

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
overhead was addressed upstream. Configurable picking, Interactions, multiview,
compression, worker offload, and shared-memory transport remain post-1.0. See
[`pending_proposals/README.md`](pending_proposals/README.md).

## Post-1.0

- Advanced MVS annotation machinery.
- Interactions domain and Studio subpanel.
- Configurable canvas picking level.
- Multi-view/split-screen synchronization.
- Lazy structure sources and partial materialization.
- Large-system rendering tiers that require Mol* upstream work.
- Cross-platform standalone packaging.
- Advanced rendering and cinematic/VR directions.

## Decision filter

Prefer work that:

- improves a real scientific workflow;
- preserves reproducibility;
- has a measurable bottleneck or verified defect;
- reuses MolSysMT and Mol* rather than duplicating scientific or rendering
  engines;
- keeps Jupyter, export, popup, and standalone behavior aligned.
