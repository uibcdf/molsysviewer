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

## → Tag 1.0.0
Released when the `0.19.0` dogfooding and validation produce no new surprises.

---

## Post-1.0 — Escalabilidad y Distribución

Tasks that extend the reach and automation of the project but do not block the initial stable release.

| # | Task | Notes | Status |
|---|---|---|---|
| 11 | **Scientific Tutorials**: 3-5 case-driven notebooks | Focus on real problems (Pocket Contact Analysis, Conformational Comparison, Pharmacophore Model). Postponed to post-1.0 to wait until sibling tools (`elastnetmt`, `pharmacophoremt`, `molsysmt`, `topomt`) and their respective addons are fully mature and polished. | Postponed |
| 16 | **E2E Playwright CI Automation** | Run the 10 Playwright E2E tests headlessly in GitHub Actions on every pull request | Planned |
| 17 | **macOS & Windows Standalone Support** | Build and publish PySide6/QtWebEngine conda recipes for macOS and Windows | Planned |
| 18 | Add Windows to CI matrix | Standard runner compatibility verification | Planned |
| 19 | Add Python 3.13 to CI matrix | Upgrade testing environment; local development already uses Python 3.13, CI currently covers 3.11-3.12 because the conda `smonitor` build set no longer resolves for Python 3.10 | Planned |
