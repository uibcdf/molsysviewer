# Showcase Governance Directives (`docs/content/showcase/AGENTS.md`)

This file defines governance rules for all showcase demonstrations and interactive feature showcases under `docs/content/showcase/`.

---

## 🎨 Showcase Philosophy

1. **High Visual Impact:** Showcases highlight advanced scientific overlays (pockets, pharmacophores, channels, anisotropy ellipsoids) and addon capabilities with publication-quality renders.
2. **Interactive 3D Views:** Embedded views MUST be pre-generated HTML views with `background="transparent"` stored in `docs/_static/views/`.
3. **Reproducibility:** Every showcase MUST include the complete, copy-pasteable Python code used to generate the scene.

---

## 🔒 Canonical Naming and Invariants

1. **View Variable:** The main `MolSysViewer` view instance MUST be named `view`.
2. **System Variable:** The underlying molecular system object MUST be named `molsys`.
