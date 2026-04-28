# Path to 1.0

Recorded 2026-04-28 after a full repository audit.

This document is the working plan for the 1.0 release.
It is ordered by milestone and updated as items are completed.

---

## 0.18.x — poner la casa en orden

Work done against the current tag (0.18.0).

| # | Task | Owner | Status |
|---|---|---|---|
| 1 | Rewrite README (current features, real API, no "prototype") | Claude | ✅ 2026-04-28 |
| 2 | Fix `pyproject.toml`: classifiers, keywords, description | Claude | ✅ 2026-04-28 |
| 3 | Fill `changes_notes.md`: entries post-2026-04-26 (region_tags, movie, JS test suite) | Claude | ✅ 2026-04-28 |
| 4 | Fill 3 placeholder doc pages (`demo_systems/catalog`, `demo_systems/index`, `scene_management/visibility`) | Claude | ✅ 2026-04-28 |
| 5 | Manual smoke test — 14-step flow in `devguide/smoke_test.md` | Diego (display) | — |
| 6 | Visual smoke of `controls_mode="minimal"` + `panel_mode_style="floating"` in a real notebook | Diego (display) | — |
| 7 | Publish conda + npm packages for `0.18.0` | Diego (credentials) | — |

---

## 0.19.0 — estabilización, dogfooding y features finales

| # | Task | Owner | Notes |
|---|---|---|---|
| 8 | Run the 5 tutorial notebooks in a real environment; fix discrepancies | Diego + Claude | |
| 9 | Scientific dogfooding in the lab — collect friction and real bugs | Diego | |
| 10 | Fix bugs and UX roughness from dogfooding | Claude | |
| 11 | Fill remaining incomplete docs | Claude | |
| 12 | **Focus Styles**: cumulative data-driven styles (`+ Hydrophobicity`, `+ H-Bonds` over existing scene) | Claude | Design in `devguide/v1_vision_and_styles.md` |
| 13 | **Box merging logic**: deterministic box display when merging systems with different unit cells | Claude | Waiting on MolSysMT API |
| 14 | **Orientation plane API**: orientation axes and best-fit plane via Mol* built-ins | Claude | Low priority — `devguide/pending_proposals/PROPOSAL_orientation_plane_api.md` |

---

## → Tag 1.0.0

Released when 0.19.0 dogfooding produces no new surprises.

---

## Post-1.0

| # | Task | Notes |
|---|---|---|
| 15 | Add Windows to CI matrix | |
| 16 | Add Python 3.13 to CI matrix | |
