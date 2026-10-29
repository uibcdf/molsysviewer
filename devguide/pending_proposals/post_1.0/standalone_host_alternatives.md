---
summary: Evaluate alternatives to Qt for a future standalone host
issue: uibcdf/molsysviewer#276
status: open
opened: 2026-10-29
closed:
verification: inspected
area: [standalone, architecture, packaging]
guard:
normative:
blocked_by: []
supersedes: []
---

# Evaluate alternatives to Qt after 1.0

**Reported:** maintainer discussion on 2026-10-29. Deferred to the post-1.0
milestone; no migration, package or release is authorized by this proposal.

## What

Compare the modernized Qt host with Electron and Tauri while preserving the
shared viewer, Python API and scientific ownership. The ChatGPT Linux desktop
application is the maintainer's visual reference: an integrated header, calm
content and no traditional permanent menu bar. An attractive reference is a
reason to investigate, not proof of a better framework for this application.

The maintainer reports inspecting installed ChatGPT 26.1013.40934 and finding
Electron 42.3.0, BrowserWindow, React, `titleBarStyle: "hidden"` and
`titleBarOverlay`. This is attributed local-package evidence, not a claim to
have inspected the official application's public source. Do not redistribute
its contents or infer undocumented internal layers.

## How

Evaluate evolved Qt/WebEngine, Electron plus the scientific Python backend,
and Tauri plus that backend. Compare pinned prototypes using the same
scientific workloads and UI flows. Measure startup, working/peak memory,
trajectory transfer, WebGL correctness, GPU picking, exports, installer and
installed sizes. Record platform, high-DPI, accessibility, window-management,
multi-monitor, fullscreen and X11/Wayland behavior.

Include Python communication, process ownership, cancellation, recovery,
cleanup, addon panels, offline distribution, updates, signing and security
maintenance. A local HTTP server is one IPC option, not an unavoidable cost.
Keep a Rust/WASM runtime without Python as a distinct scientific/API-parity
decision; it is not a prerequisite for changing the window host.

## Why

The current Qt host already owns a live MolSysView and binary molecular
delivery. A replacement needs measured benefits that justify integration,
maintenance and distribution costs. Modernizing Qt now supplies a fair
comparison baseline. One scene/state/workbench model must remain shared
with Jupyter and popup canvases, with no weaker Python API.

## Earlier material to reconcile

- [Standalone direction](../../standalone_direction.md): one workbench, several hosts.
- [Operational host plan](../../standalone_host_plan.md): Qt preference and previous Tauri/Electron decisions.
- [Version 2 evolution plan](../../standalone_v2_evolution_plan.md): evolved Qt, Python-sidecar and WASM alternatives.
- [Packaging strategy](../../standalone_packaging_strategy.md): distribution context.
- [Archived performance/depythonization roadmap](../../archive/standalone_performance_and_depythonization.md): historical rationale; its Numba/JIT premise was retired.
- [Startup baseline](../../performance/startup_baseline_2026_07.md): measured attribution replacing old JIT figures.

Read old UI limitations, installer sizes, instant-start predictions and
security/multi-window superlatives as hypotheses requiring current evidence.
This comparison is separate from uibcdf/molsysviewer#109/#113 (Qt family and
host qualification) and #51 (Qt popout parity).

## What was refuted

Qt is not inherently restricted to a traditional menu-bar appearance. The
consumer ChatGPT example does not establish that Electron is lighter, faster
or scientifically suitable for MolSysViewer. Old Numba cold-start figures
cannot decide the host choice after the provider's Rust transition.

## Acceptance

A reviewed decision identifies exact baselines/prototypes, measured tradeoffs,
scientific/API/addon compatibility, platform limits and maintenance cost.
Retaining Qt is a valid outcome. Any migration receives a separate bounded
implementation plan and qualification gates.
