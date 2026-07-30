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
| 7 | Publish conda + npm packages for `0.18.0` | Diego | — |

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
viewer should eliminate avoidable `ViewerJSON`, nested-list, and text-JSON
coordinate amplification for structures already selected into `view.molsys`,
while preserving the current complete-materialization semantics and JSON
fallback. The same round establishes typed routing across Python, widget/Qt
hosts, embedded canvases, and popups so large payloads are not replayed or
mutated twice. Lazy structure sources, eager/windowed modes, compression,
workers, multiview, camera/movie expansion, and other product scope remain
post-1.0.

Real-window Qt/WebGL validation, scientific dogfooding (#14), end-user
distribution, and onboarding README verification remain release gates as well.

---

## → Tag 1.0.0
Released when the `0.19.0` dogfooding and validation produce no new surprises.

---

## Post-1.0 — Optimización avanzada y distribución

Tasks that extend the reach and automation of the project but do not block the initial stable release.

| # | Task | Notes | Status |
|---|---|---|---|
| 11 | **Scientific Tutorials**: 3-5 case-driven notebooks | Focus on real problems (Pocket Contact Analysis, Conformational Comparison, Pharmacophore Model). Postponed to post-1.0 to wait until sibling tools (`elastnetmt`, `pharmacophoremt`, `molsysmt`, `topomt`) and their respective addons are fully mature and polished. | Postponed |
| 16 | **E2E Playwright CI Automation** | Run the 10 Playwright E2E tests headlessly in GitHub Actions on every pull request | Planned |
| 17 | **macOS & Windows Standalone Support** | Build and publish PySide6/QtWebEngine conda recipes for macOS and Windows | Planned |
| 18 | Add Windows to CI matrix | Standard runner compatibility verification | Planned |
| 19 | Add Python 3.13 to CI matrix | Upgrade testing environment; local development already uses Python 3.13, CI currently covers 3.11-3.12 because the conda `smonitor` build set no longer resolves for Python 3.10 | Planned |
