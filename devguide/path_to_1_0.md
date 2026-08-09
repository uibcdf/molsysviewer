# Path to 1.0.0 (Unified Release Plan)

This document is the authoritative release plan for the **v1.0.0** release of MolSysViewer. 

It consolidates the strategic milestones with the competitive quality gaps (previously tracked under the confusing `path_to_8_5.md` document) to ensure that the stable `1.0.0` release reaches a high-quality competitive score (**8.5/10**) in the scientific Python ecosystem.

---

## 0.18.x — Poner la casa en orden (Completed)

Work done against the `0.18.0` tag.

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Rewrite README (current features, real API, no "prototype" mentions) | Claude | ✅ 2026-04-28 |
| 2 | Fix `pyproject.toml` metadata: classifiers, keywords, description | Claude | ✅ 2026-04-28 |
| 3 | Update `changes_notes.md` with entries post-2026-04-26 | Claude | ✅ 2026-04-28 |
| 4 | Fill 3 placeholder doc pages (`demo_systems/catalog`, `demo_systems/index`, `scene_management/visibility`) | Claude | ✅ 2026-04-28 |
| 5 | Manual smoke test — 14-step flow in `devguide/smoke_test.md` | Diego | — |
| 6 | Visual smoke of `controls_mode="minimal"` + `panel_mode_style="floating"` in a real notebook | Diego | — |
| 7 | Publish conda + npm packages | Diego | npm at `0.20.0` since 2026-08-05; conda still at `0.7.0`. npm now triggers on a pushed tag — the trigger that stopped firing at `0.8.0` and cost thirteen unpublished versions. Conda stays on a GitHub Release by decision: a tag is a checkpoint, a conda package is something people install. See `docs/content/developer/releasing.md`. |

---

## 0.19.0 — Estabilización, Dogfooding y Calidad Final (Tagged)

The `0.19.0` tag is now the clean checkpoint after the pre-`1.0.0`
devguide cleanup, pending proposal triage, CI workflow repair, and standalone Qt
backend consolidation work.

This tag should be read as a stable development checkpoint, not the final
`1.0.0` release gate. The remaining work is dogfooding, final validation, and
dependency-channel synchronization once the latest sibling packages are
published.

### 1. Technical Features & Infrastructure
| # | Task | Notes | Status |
|---|---|---|---|
| 8 | **Focus Styles**: Cumulative data-driven styles (`styles.focus()`, `clear_focus()`) | Allows highlighting regions (e.g. `+ Hydrophobicity` or `+ H-Bonds`) | ✅ 2026-04-28 |
| 9 | **Orientation Plane API**: Axes and best-fit planes (`show_orientation_axes()`, `show_best_fit_plane()`) | Exposes Mol* principal axes and best-fit plane representations | ✅ 2026-04-28 |
| 10 | **Box Merging Logic**: Deterministic unit-cell display when merging systems | Audited: identified as a MolSysMT-side change (requires no code change in viewer) | 🔍 Audited |

### 2. Scientific Adoption & Onboarding
| # | Task | Notes | Status |
|---|---|---|---|
| 12 | **First-Contact Onboarding**: Simplify README quickstart | Show the 10-line synergy: MolSysMT reads anything ➔ MolSysViewer displays it | Pending after `0.19.0` |
| 13 | **Surface & UX Polish**: Close minor interaction gaps | Add scroll inside the `GroupStrip` for large systems; improve context menu status feedback | ✅ 2026-06-24 |

### 3. Validation & Hardening
| # | Task | Notes | Status |
|---|---|---|---|
| 14 | **Scientific Dogfooding**: Daily lab usage | Collect real-world friction and identify edge cases or bugs | Pending after `0.19.0` |
| 15 | **Bug Resolution**: Fix findings from dogfooding | Address any stability or usability bugs raised by researchers | Pending after `0.19.0` |

Current CI note:

- `CI_e2e` is green at the `0.19.0` checkpoint.
- The main GitHub CI workflow has been repaired structurally, but its final
  green state is temporarily gated by the publication cadence of sibling
  dependency packages in conda, especially APIs from `smonitor` used by the
  current MolSysViewer code.

---

## Post-`0.19.0` — Saneamiento y endurecimiento hacia `1.0.0` (2026-07)

Work done after the `0.19.0` checkpoint, executing the "bug resolution" gate (#15) as a
systematic audit rather than only through dogfooding. Each item was verified by mutation testing.

### Core runtime and contracts — the scene-objects block (9 phases)
Closed the conceptual confusion the Fase D gate warned about. Established normative contracts
(`devguide/scene_contracts.md`): identity is `(domain, tag)` not `tag` (T); every scene domain has
one canonical manager surface (S0); Python is the single source of truth (S1); the GUI acts only
through the public API (S2); restore rebuilds the live model, not a zombie (S5); undo with coalescing
(S6); a damaged anchor is a *state*, never a silent deletion nor a stale number (S7). The four Studio
subpanels (Measures, Annotations, Shapes, Layers) were built on that base. **This resolved the core
runtime's "conceptual confusion", which the roadmap Fase D required for `1.0.0`.**

### Product tightening — real defects removed before dogfooding could hit them
- **Public output follows the configured default unit** (PyUnitWizard `standardize`), instead of
  hardcoding ångströms — factory default is nm; a user-selected standard is respected end to end.
- **Clipping-plane sections persist** end to end and are managed from Studio → Viewport.
- **Widget/view lifecycle leak fixed** — a discarded `MolSysView` no longer leaks through the global
  ipywidgets registry; `MolSysView.close()` and context-manager cleanup added.
- **Scene-object `owner`** records add-on provenance (Fase B credibility).
- **E2E reliability**: the browser E2E suites now fail loudly when the browser cannot start, instead
  of passing in false green.

### Fase E closed for real — standalone Qt audit + Q1–Q5
The roadmap already marked *"host-side error handling no longer silent ✓"*. A full audit
([`devguide/audits/standalone_qt_audit_2026_07.md`](audits/standalone_qt_audit_2026_07.md))
found it was **not** true and closed the five gaps:
Q1 swallowed view-event exceptions, Q2 a bridge that could stall or retry forever, Q3 unvalidated
malformed events, Q4 a delivery guarantee the docs promised but the code did not keep, Q5 silent
persistence failures. **That ✓ is now genuinely true.** The only Fase E item still open is the
real-window Qt/WebGL validation, which requires a real display/GPU.

### Ecosystem
The **ElasNetMT add-on was renamed to ElastNetMT** across both repositories.

**Reading:** scene and product contracts are mature, but the July 2026 transport
baseline exposed one remaining transport requirement. Before `1.0.0`, the
viewer should eliminate avoidable intermediate-form, nested-list, and text-JSON
coordinate amplification for structures already selected into `view.molsys`,
while preserving the current complete-materialization semantics and JSON
fallback. The same round establishes typed routing across Python, widget/Qt
hosts, embedded canvases, and popups so large payloads are not replayed or
mutated twice. Lazy structure sources, eager/windowed modes, compression,
workers, multiview, camera/movie expansion, and other product scope remain
post-1.0.

Scientific dogfooding (#14), end-user distribution, and onboarding README
verification remain release gates as well. Qt was validated on a real GPU, but
the current camera-authority and live-reload paths still need the visible-window
revalidation recorded in Phase 7. GPU-runner CI remains post-1.0.

---

## Transport, routing and honest limits (2026-07-30/31)

The round the reading above called for, delivered and verified by mutation.

### Runtime envelopes and single authority (R0–R2)
A shared manifest (`molsysviewer/runtime_actions.json`) classifies every
browser-originated action; Python and TypeScript load the same file, so both
classify identically by construction. Python is the only authority: identity,
direction and action↔payload coherence are validated, and `command` messages are
deduplicated so one accepted command yields one public-API mutation and one
history checkpoint. Enveloping lives in the connector (`MolSysViewerWidget.send`),
so Qt stays raw and history keeps domain messages.

The popup no longer bootstraps from a replay journal: `build_popup_scene_snapshot`
rebuilds the current scene from the live registries, pure with respect to history
and transport. Inflating the journal with 10,000 unrelated ops leaves the
snapshot byte-for-byte identical.

### Array-native data plane (D0–D4)
Coordinates travel in a planar layout so Mol\* frames are zero-copy views,
removing a per-frame de-interleaving pass at no cost in Python. An
acknowledgement deadline releases retained arrays and falls back observably
without a timer thread, which would make `widget.send` unsafe off the kernel
thread. A canvas popup receives its own typed molecular generation, relayed by
the host without retaining anything, which lifted the restriction that disabled
the binary path whenever popout was enabled.

### Honest limits instead of silent failures
1.0 deliberately keeps complete materialization, so a load large enough to
exhaust the browser tab now warns with the measured size and a concrete
`structure_indices` subset that fits (`set_structure_scale_budget`). Windowed
residency stays post-1.0 because it changes what `view.molsys` means and its
failure mode is silently wrong science. `SharedArrayBuffer` was reclassified
from post-1.0 to **blocked on external preconditions**: COOP/COEP belong to the
notebook host, and Mol\* reorders coordinate arrays in place.

### Two guards for defect classes that hid under a green suite
- **Digester callers.** The boundary audit asked whether a digester existed and
  found 26 missing. It never asked whether the digester accepts the viewer
  calling it. 58 of 81 query arguments rejected `molsysviewer.viewer.get`, so
  `view.get(...)` was broken for nearly its whole surface, for months, with
  every test green. Fixed and guarded.
- **Documentation execution.** Sphinx does not execute notebooks, so a previous
  API hardening broke ten documented notebooks unnoticed. All are green again;
  putting `docs/execute_notebooks.py` in CI is still open (see gates below).

### Correction to this document
Item 16 (*E2E Playwright CI Automation*) was listed as `Planned`. `CI_e2e.yaml`
already runs `npm run test:e2e` on every pull request to `main`. **Done.**
Deciding release readiness against a stale plan is its own risk.

---

## Remaining `1.0.0` gates

| # | Gate | Notes |
|---|---|---|
| 20 | **Qt parity (R3) and its own benchmark** | ✅ done. The benchmark measured 4.3 s of Python preparation for 5,000 structures against 36 ms array-native, so Qt now serves raw arrays through the scheme handler it already had. R3 closed a real fork: an unknown action was rejected observably on AnyWidget and accepted in silence on Qt. |
| 22 | **Notebook execution in CI** | **Done** — `.github/workflows/docs-notebooks.yaml`; see [`archive/documentation_execution_in_ci.md`](archive/documentation_execution_in_ci.md). `docs/execute_notebooks.py` is the real check; Sphinx does not execute notebooks, which is how ten broken ones survived unnoticed. |
| 25 | **Legacy popup vocabulary** | ✅ done. The eleven host/popup actions are declared in a `popup_actions` group with the directions each may carry, and both ends validate against it. `molsysviewer-sync-op` is declared bidirectional, which makes explicit the ambiguity that motivated the envelope in the first place. |
| 23 | **Widget seam E2E** | ✅ done. `widget-seam.e2e.ts` drives the real `render()` in Chromium: raw `ready`, enveloped outbound, a valid projection reaching the controller, and a foreign session never reaching it. |
| 24 | **R2 tail** | ✅ done. The journal is gone from the interactive path — kept only in `bootDocsView`, where a static export has no Python to ask — and `build_context_items` is the pure half that lets the panel snapshot carry add-on context items. |
| 26 | **Architecture rework and hardening** | In progress. Phases 0a–6, 8 and 9 are audited; Phase 7 awaits two visible Qt observations. Phase 10 has closed notebook CI, state-file persistence and hover semantics; dependency-channel closure, final installed-artifact reruns, dogfooding and the final matrix remain. See [`pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md`](pending_proposals/pre_1_0_architecture_rework_and_hardening_master_plan.md). |
| 14 | **Scientific dogfooding** | Unchanged: daily lab usage is what finds what audits cannot. |
| 15 | **Bug resolution from dogfooding** | Unchanged. |

---

## → Tag 1.0.0
Released when the gates above are closed and dogfooding produces no new
surprises. Note before tagging: `_version.py` is a git-ignored artifact and
`package.json` is generated from it, so both must be regenerated from the
repository or the published version will be wrong.

---

## Post-1.0 — Optimización avanzada y distribución

Tasks that extend the reach and automation of the project but do not block the initial stable release.

| # | Task | Notes | Status |
|---|---|---|---|
| 11 | **Scientific Tutorials**: 3-5 case-driven notebooks | Focus on real problems (Pocket Contact Analysis, Conformational Comparison, Pharmacophore Model). Postponed to post-1.0 to wait until sibling tools (`elastnetmt`, `pharmacophoremt`, `molsysmt`, `topomt`) and their respective addons are fully mature and polished. | Postponed |
| 16 | **E2E Playwright CI Automation** | `CI_e2e.yaml` runs `npm run test:e2e` on every pull request to `main` | ✅ done (this entry was stale) |
| 21 | **Qt render check on a GPU runner** | Moved out of the 1.0 gates: the render itself is already validated on real GPU, and Decision 1 classifies the CI job as level 2, non-blocking. See [`pending_proposals/post_1.0/qt_render_check_on_a_gpu_runner.md`](pending_proposals/post_1.0/qt_render_check_on_a_gpu_runner.md). Needs a machine with a GPU **and a graphical session**. | Post-1.0 |
| 17 | **macOS & Windows Standalone Support** | Build and publish PySide6/QtWebEngine conda recipes for macOS and Windows | Planned |
| 18 | Add Windows to CI matrix | Standard runner compatibility verification | Planned |
| 19 | Add Python 3.13 to CI matrix | Upgrade testing environment; local development already uses Python 3.13, CI currently covers 3.11-3.12 because the conda `smonitor` build set no longer resolves for Python 3.10 | Planned |
