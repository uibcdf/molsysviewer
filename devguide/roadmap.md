# Development roadmap

**Updated:** 2026-09-02

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
5. End-user installation and dependency-channel synchronization.
6. First-contact README/onboarding verification.
7. Documentation and package-version consistency at the release commit.
8. Close the decided `@digest` policy over the supported public callable
   surface, with argument digesters and catalogued diagnostics rather than
   decoration-only coverage.
9. Deliver the accepted single-user remote-session slice: explicit
   `render_on="client" | "server"`, browser and Qt clients, managed real-GPU
   render worker, VP8 WebRTC transport, authenticated session routing and the
   documented spika-to-nauta acceptance path. See
   [`remote_rendering_plan.md`](remote_rendering_plan.md). RRS0 and RRS1 are
   complete. RRS2 is complete: the server-rendered browser workflow covers the managed
   worker, array-native loading, authenticated VP8 video/input, controller-free
   workbench and trajectory controls, upload/export and reconnect. Browser
   client rendering now uses the same gateway and exact full frontend entrypoint
   and has portable WebGL/array-native, reconnect, direct canvas camera/picking,
   authoritative Whole/selection/trajectory actions, local-PNG/canonical-HTML
   export and authenticated replacement-upload E2E evidence. RRS3 now has the
   shared Qt `--connect` shell, native menus/shortcuts, upload activation and
   save-dialog-managed downloads; visible nauta acceptance, followed by RRS4
   hardening, remains. RRS4 lifecycle work now includes one bounded automatic
   render-worker recovery with canonical scene retransmission and WebRTC
   renegotiation, plus a static-scene-safe video-stall watchdog. Shared visible
   connection states and the loopback token/origin/rate/size/session-isolation
   baseline are now guarded; clean deployment and visible nauta acceptance
   remain. The 1.0 deployment
   surface includes a public `molsysviewer-server` command limited to one
   foreground session. Background services, durable/multi-session management,
   institutional identity, managed TURN, scheduler integration, GPU pools and
   MolSys-AI lifecycle remain post-1.0 and must compose the same session API.

## Active pre-1.0 execution

The transport and routing contracts landed in gates 1 and 2. The architecture
rework found by the subsequent repository audit and JupyterLab smoke testing is
implemented through Phase 8: typed transfer lifecycle, lazy generation-bound
fallback, canonical static/live projection, endpoint ownership, seam evidence
and representative performance/memory gates. Phase 9 reconciled durable
documentation; Phase 10 owns the remaining product/release gates. The canonical
dashboard is
[`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pre_1_0_architecture_rework_and_hardening_master_plan.md).

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
